# Source Generated with Decompyle++
# File: 022.pyc (Python 3.10)

if self.dragging or event.buttons() & Qt.LeftButton:
    self._set_drag_value(self._value(event.y() if self.orientation == Qt.Vertical else event.x()))
    return None
return None
