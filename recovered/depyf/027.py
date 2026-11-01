def DragOnlySlider():
    __module__ = __name__
    __qualname__ = 'DragOnlySlider'
    
    
    def __init__(self, orientation, parent):
        nonlocal __class__
        super().__init__(orientation, parent)
        self._dragging_handle = False
        return None
    
    
    def wheelEvent(self, event):
        event.ignore()
        return None
    
    
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
    
    
    def mouseMoveEvent(self, event):
        nonlocal __class__
        if self._dragging_handle:
            super().mouseMoveEvent(event)
            return None
        event.ignore()
        return None
    
    
    def mouseReleaseEvent(self, event):
        nonlocal __class__
        if self._dragging_handle:
            super().mouseReleaseEvent(event)
            self._dragging_handle = False
        else:
            self._dragging_handle = False
        return None
    
    
    __classcell__ = __class__
    return __class__
