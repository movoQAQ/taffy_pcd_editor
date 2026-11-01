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
