def _set_drag_value(self, value):
    if self.dragging == 'low':
        self.low = min(max(value, 0), self.high - 1)
    elif self.dragging == 'high':
        self.high = max(min(value, 1000), self.low + 1)
    self.update()
    self.rangeChanged.emit(self.low, self.high)
    return None
