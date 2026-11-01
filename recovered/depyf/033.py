def LayerSelectButton():
    __module__ = __name__
    __qualname__ = 'LayerSelectButton'
    doubleClicked = pyqtSignal()
    
    
    def mouseDoubleClickEvent(self, event):
        nonlocal __class__
        if event.button() == Qt.LeftButton:
            self.doubleClicked.emit()
            event.accept()
            return None
        super().mouseDoubleClickEvent(event)
        return None
    
    
    __classcell__ = __class__
    return __class__
