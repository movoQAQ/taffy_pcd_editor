def EmbeddedVTKWidget():
    __module__ = __name__
    __qualname__ = 'EmbeddedVTKWidget'
    doubleClicked = pyqtSignal(int, int)
    
    
    def setPointPickMode(self, enabled):
        self._point_pick_mode = bool(enabled)
        return None
    
    
    def mouseDoubleClickEvent(self, event):
        nonlocal __class__
        if event.button() == Qt.LeftButton:
            if getattr(self, '_point_pick_mode', False):
                __temp_4783, __temp_4784 = self.GetRenderWindow().GetSize()
                render_width = __temp_4783
                render_height = __temp_4784
                if render_width > 0:
                    if render_height > 0:
                        x = round(event.x() * render_width / self.width())
                        y = round((self.height() - event.y() - 1) *
                            render_height / self.height())
                        self.doubleClicked.emit(x, y)
                        super().mousePressEvent(event)
                        return None
                    else:
                        super().mousePressEvent(event)
                        return None
                else:
                    super().mousePressEvent(event)
                    return None
            else:
                super().mousePressEvent(event)
                return None
        else:
            super().mousePressEvent(event)
            return None
    
    
    def winId(self):
        nonlocal __class__
        self.setAttribute(Qt.WA_DontCreateNativeAncestors, True)
        return super().winId()
    
    
    __classcell__ = __class__
    return __class__
