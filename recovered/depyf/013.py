def HeightRangeSlider():
    __module__ = __name__
    __qualname__ = 'HeightRangeSlider'
    rangeChanged = pyqtSignal(int, int)
    
    
    def __init__(self, orientation, parent):
        nonlocal __class__
        super().__init__(parent)
        self.orientation = orientation
        self.setStyleSheet(
            'background:#fff8fd;border:1px solid #eaddea;border-radius:8px;')
        self.setFocusPolicy(Qt.StrongFocus)
        self.low = 0
        self.high = 1000
        self.dragging = None
        if orientation == Qt.Vertical:
            self.setFixedWidth(32)
            self.setMinimumHeight(140)
            return None
        self.setFixedHeight(32)
        self.setMinimumWidth(180)
        return None
    
    
    def _track(self):
        if self.orientation == Qt.Vertical:
            extent = self.height()
        else:
            extent = self.width()
        start = 12
        end = extent - 12
        return start, max(start + 1, end)
    
    
    def _y(self, value):
        __temp_4552, __temp_4553 = self._track()
        start = __temp_4552
        end = __temp_4553
        if self.orientation == Qt.Vertical:
            return end - (end - start) * value / 1000
        return start + (end - start) * value / 1000
    
    
    def _value(self, coordinate):
        __temp_4555, __temp_4556 = self._track()
        start = __temp_4555
        end = __temp_4556
        if self.orientation == Qt.Vertical:
            value = (end - coordinate) / (end - start) * 1000
        else:
            value = (coordinate - start) / (end - start) * 1000
        return int(np.clip(round(value), 0, 1000))
    
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        __temp_4563, __temp_4564 = self._track()
        start = __temp_4563
        end = __temp_4564
        if self.orientation == Qt.Vertical:
            center = self.width() // 2
            """original function name <lambda> is illegal, use a temp name."""
    
            def point(value):
                nonlocal center, self
                return center, round(self._y(value))
        else:
            center = self.height() // 2
            """original function name <lambda> is illegal, use a temp name."""
    
            def point(value):
                nonlocal center, self
                return round(self._y(value)), center
        a = point(0)
        b = point(1000)
        painter.setPen(QPen(QColor('#c9b8cc'), 6, Qt.SolidLine, Qt.RoundCap))
        __temp_4579 = []
        __temp_4579.extend(a)
        __temp_4580 = __temp_4579
        __temp_4580.extend(b)
        painter.drawLine(*tuple(__temp_4580))
        painter.setPen(QPen(QColor('#d96196'), 3, Qt.SolidLine, Qt.RoundCap))
        __temp_4587 = []
        __temp_4587.extend(point(self.low))
        __temp_4589 = __temp_4587
        __temp_4589.extend(point(self.high))
        painter.drawLine(*tuple(__temp_4589))
        for __temp_4591 in iter((self.high, self.low)):
            value = __temp_4591
            painter.setPen(QPen(QColor('#d9a8bf'), 1))
            painter.setBrush(QColor('#ffffff'))
            __temp_4598, __temp_4599 = point(value)
            x = __temp_4598
            y = __temp_4599
            painter.drawEllipse(x - 6, y - 6, 12, 12)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor('#9d3b6c'))
            painter.drawEllipse(x - 3, y - 3, 6, 6)
            continue
        return None
    
    
    def mousePressEvent(self, event):
        if event.button() != Qt.LeftButton:
            return None
        if self.orientation == Qt.Vertical:
            value = self._value(event.y())
        else:
            value = self._value(event.x())
        if abs(value - self.low) < abs(value - self.high):
            self.dragging = 'low'
        else:
            self.dragging = 'high'
        self._set_drag_value(value)
        return None
    
    
    def mouseMoveEvent(self, event):
        if self.dragging:
            if event.buttons() & Qt.LeftButton:
                if self.orientation == Qt.Vertical:
                    self._set_drag_value(self._value(event.y()))
                    return None
                else:
                    self._set_drag_value(self._value(event.x()))
                    return None
                return None
        else:
            return None
        return None
    
    
    def mouseReleaseEvent(self, event):
        self.dragging = None
        return None
    
    
    def keyPressEvent(self, event):
        nonlocal __class__
        if event.key() not in (Qt.Key_Up, Qt.Key_Down, Qt.Key_Left, Qt.Key_Right):
            return super().keyPressEvent(event)
        if self.dragging != 'high':
            self.dragging = 'low'
        else:
            self.dragging = 'high'
        if event.key() in (Qt.Key_Up, Qt.Key_Right):
            delta = 10
        else:
            delta = -10
        if self.dragging == 'low':
            self._set_drag_value(self.low + delta)
            return None
        else:
            self._set_drag_value(self.high + delta)
            return None
    
    
    def _set_drag_value(self, value):
        if self.dragging == 'low':
            self.low = min(max(value, 0), self.high - 1)
        elif self.dragging == 'high':
            self.high = max(min(value, 1000), self.low + 1)
        self.update()
        self.rangeChanged.emit(self.low, self.high)
        return None
    
    
    def set_range(self, low, high):
        self.low = low
        self.high = high
        self.update()
        return None
    
    
    __classcell__ = __class__
    return __class__
