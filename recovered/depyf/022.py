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
