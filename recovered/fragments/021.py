# Source Generated with Decompyle++
# File: 021.pyc (Python 3.10)

if event.button() != Qt.LeftButton:
    return None
value = None._value(event.y() if self.orientation == Qt.Vertical else event.x())
self.dragging = 'low' if abs(value - self.low) < abs(value - self.high) else 'high'
self._set_drag_value(value)
