# Source Generated with Decompyle++
# File: 061.pyc (Python 3.10)

completed = pyqtSignal(int, int, int)

def __init__(self = None, request_id = None, layer_id = None, points = None, ranges = None):
    super().__init__()
    self.request_id = request_id
    self.layer_id = layer_id
    self.points = points
    self.ranges = ranges


def run(self):
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

__classcell__ = None
