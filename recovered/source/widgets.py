"""Standalone Qt sliders recovered from the v1.2 code objects 013–032.

Defaults, signals, painting and event branches checked against Python 3.10 dis.
This module does not load the original bytecode.
"""
import numpy as np
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor, QPainter, QPen
from PyQt5.QtWidgets import QSlider, QStyle, QStyleOptionSlider, QWidget


class HeightRangeSlider(QWidget):
    rangeChanged = pyqtSignal(int, int)

    def __init__(self, orientation=Qt.Vertical, parent=None):
        super().__init__(parent)
        self.orientation = orientation
        self.setStyleSheet('background:#fff8fd;border:1px solid #eaddea;border-radius:8px;')
        self.setFocusPolicy(Qt.StrongFocus)
        self.low = 0
        self.high = 1000
        self.dragging = None
        if orientation == Qt.Vertical:
            self.setFixedWidth(32)
            self.setMinimumHeight(140)
        else:
            self.setFixedHeight(32)
            self.setMinimumWidth(180)

    def _track(self):
        extent = self.height() if self.orientation == Qt.Vertical else self.width()
        start = 12
        end = extent - 12
        return start, max(start + 1, end)

    def _y(self, value):
        start, end = self._track()
        if self.orientation == Qt.Vertical:
            return end - (end - start) * value / 1000
        return start + (end - start) * value / 1000

    def _value(self, coordinate):
        start, end = self._track()
        if self.orientation == Qt.Vertical:
            value = (end - coordinate) / (end - start) * 1000
        else:
            value = (coordinate - start) / (end - start) * 1000
        return int(np.clip(round(value), 0, 1000))

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        start, end = self._track()
        if self.orientation == Qt.Vertical:
            center = self.width() // 2
            point = lambda value: (center, round(self._y(value)))
        else:
            center = self.height() // 2
            point = lambda value: (round(self._y(value)), center)
        a, b = point(0), point(1000)
        painter.setPen(QPen(QColor('#c9b8cc'), 6, Qt.SolidLine, Qt.RoundCap))
        painter.drawLine(*a, *b)
        painter.setPen(QPen(QColor('#d96196'), 3, Qt.SolidLine, Qt.RoundCap))
        painter.drawLine(*point(self.low), *point(self.high))
        for value in (self.high, self.low):
            painter.setPen(QPen(QColor('#d9a8bf'), 1))
            painter.setBrush(QColor('#ffffff'))
            x, y = point(value)
            painter.drawEllipse(x - 6, y - 6, 12, 12)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor('#9d3b6c'))
            painter.drawEllipse(x - 3, y - 3, 6, 6)

    def mousePressEvent(self, event):
        if event.button() != Qt.LeftButton:
            return
        value = self._value(event.y() if self.orientation == Qt.Vertical else event.x())
        self.dragging = 'low' if abs(value - self.low) < abs(value - self.high) else 'high'
        self._set_drag_value(value)

    def mouseMoveEvent(self, event):
        if self.dragging and event.buttons() & Qt.LeftButton:
            self._set_drag_value(self._value(event.y() if self.orientation == Qt.Vertical else event.x()))

    def mouseReleaseEvent(self, event):
        self.dragging = None

    def keyPressEvent(self, event):
        if event.key() not in (Qt.Key_Up, Qt.Key_Down, Qt.Key_Left, Qt.Key_Right):
            return super().keyPressEvent(event)
        self.dragging = 'low' if self.dragging != 'high' else 'high'
        delta = 10 if event.key() in (Qt.Key_Up, Qt.Key_Right) else -10
        self._set_drag_value((self.low if self.dragging == 'low' else self.high) + delta)

    def _set_drag_value(self, value):
        if self.dragging == 'low':
            self.low = min(max(value, 0), self.high - 1)
        elif self.dragging == 'high':
            self.high = max(min(value, 1000), self.low + 1)
        self.update()
        self.rangeChanged.emit(self.low, self.high)

    def set_range(self, low, high):
        self.low = low
        self.high = high
        self.update()


class DragOnlySlider(QSlider):
    def __init__(self, orientation, parent=None):
        super().__init__(orientation, parent)
        self._dragging_handle = False

    def wheelEvent(self, event):
        event.ignore()

    def mousePressEvent(self, event):
        option = QStyleOptionSlider()
        self.initStyleOption(option)
        handle = self.style().subControlRect(QStyle.CC_Slider, option, QStyle.SC_SliderHandle, self)
        if event.button() != Qt.LeftButton or not handle.adjusted(-5, -5, 5, 5).contains(event.pos()):
            event.ignore()
            return
        self._dragging_handle = True
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._dragging_handle:
            super().mouseMoveEvent(event)
        else:
            event.ignore()

    def mouseReleaseEvent(self, event):
        if self._dragging_handle:
            super().mouseReleaseEvent(event)
        self._dragging_handle = False
