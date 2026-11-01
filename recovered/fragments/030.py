# Source Generated with Decompyle++
# File: 030.pyc (Python 3.10)

option = QStyleOptionSlider()
self.initStyleOption(option)
handle = self.style().subControlRect(QStyle.CC_Slider, option, QStyle.SC_SliderHandle, self)
if not event.button() != Qt.LeftButton or handle.adjusted(-5, -5, 5, 5).contains(event.pos()):
    event.ignore()
    return None
self._dragging_handle = None
super().mousePressEvent(event)
