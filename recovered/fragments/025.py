# Source Generated with Decompyle++
# File: 025.pyc (Python 3.10)

if self.dragging == 'low':
    self.low = min(max(value, 0), self.high - 1)
elif self.dragging == 'high':
    self.high = max(min(value, 1000), self.low + 1)
self.update()
self.rangeChanged.emit(self.low, self.high)
