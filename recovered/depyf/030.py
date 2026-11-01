def mousePressEvent(self, event):
    nonlocal __class__
    option = QStyleOptionSlider()
    self.initStyleOption(option)
    handle = self.style().subControlRect(QStyle.CC_Slider, option, QStyle.
        SC_SliderHandle, self)
    if not event.button() != Qt.LeftButton:
        if not handle.adjusted(-5, -5, 5, 5).contains(event.pos()):
            event.ignore()
            return None
    else:
        event.ignore()
        return None
    self._dragging_handle = True
    super().mousePressEvent(event)
    return None
