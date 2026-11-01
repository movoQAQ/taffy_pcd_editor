# Source Generated with Decompyle++
# File: 057.pyc (Python 3.10)

completed = pyqtSignal(int, object, int)
failed = pyqtSignal(int, str)

def __init__(self = None, request_id = None, points = None, equations = None, bounds = None, visible_ranges = None):
    super().__init__()
    self.request_id = request_id
    self.points = points
    self.equations = equations.copy()
    self.bounds = tuple((lambda .0: for bound in .0:
bound.copy())(bounds))
    self.visible_ranges = visible_ranges.copy()


def run(self):
    pass
# WARNING: Decompyle incomplete

__classcell__ = None
