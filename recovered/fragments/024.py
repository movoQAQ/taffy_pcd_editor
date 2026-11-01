# Source Generated with Decompyle++
# File: 024.pyc (Python 3.10)

if event.key() not in (Qt.Key_Up, Qt.Key_Down, Qt.Key_Left, Qt.Key_Right):
    return super().keyPressEvent(event)
self.dragging = 'low' if None.dragging != 'high' else 'high'
delta = 10 if event.key() in (Qt.Key_Up, Qt.Key_Right) else -10
self._set_drag_value(self.low if self.dragging == 'low' else self.high + delta)
