# Source Generated with Decompyle++
# File: 027.pyc (Python 3.10)


def __init__(self = None, orientation = None, parent = None):
    super().__init__(orientation, parent)
    self._dragging_handle = False


def wheelEvent(self, event):
    event.ignore()


def mousePressEvent(self = None, event = None):
    option = QStyleOptionSlider()
    self.initStyleOption(option)
    handle = self.style().subControlRect(QStyle.CC_Slider, option, QStyle.SC_SliderHandle, self)
    if not event.button() != Qt.LeftButton or handle.adjusted(-5, -5, 5, 5).contains(event.pos()):
        event.ignore()
        return None
    self._dragging_handle = None
    super().mousePressEvent(event)


def mouseMoveEvent(self = None, event = None):
    if self._dragging_handle:
        super().mouseMoveEvent(event)
        return None
    None.ignore()


def mouseReleaseEvent(self = None, event = None):
    if self._dragging_handle:
        super().mouseReleaseEvent(event)
    self._dragging_handle = False

__classcell__ = None
