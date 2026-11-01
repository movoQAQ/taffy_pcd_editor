# Source Generated with Decompyle++
# File: 063.pyc (Python 3.10)

count = 0
for start in range(0, len(self.points), 1000000):
    if self.isInterruptionRequested():
        return None
    chunk = None.points[start:start + 1000000]
    inside = np.ones(len(chunk), bool, **('dtype',))
    for column, axis in enumerate('xyz'):
        (low, high) = self.ranges[axis]
        inside &= (chunk[(:, column)] >= low) & (chunk[(:, column)] <= high)
    count += int(np.count_nonzero(inside))
self.completed.emit(self.request_id, self.layer_id, count)
