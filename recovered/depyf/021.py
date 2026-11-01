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
