# Source Generated with Decompyle++
# File: 013.pyc (Python 3.10)

rangeChanged = pyqtSignal(int, int)

def __init__(self = None, orientation = None, parent = None):
    super().__init__(parent)
    self.orientation = orientation
    self.setStyleSheet('background:#fff8fd;border:1px solid #eaddea;border-radius:8px;')
    self.setFocusPolicy(Qt.StrongFocus)
    self.low = 0
    self.high = 1000
    self.dragging = None
    if orientation == Qt.Vertical:
        self.setFixedWidth(32)
        self.setMinimumHeight(140)
        return None
    None.setFixedHeight(32)
    self.setMinimumWidth(180)


def _track(self):
    extent = self.height() if self.orientation == Qt.Vertical else self.width()
    start = 12
    end = extent - 12
    return (start, max(start + 1, end))


def _y(self, value):
    (start, end) = self._track()
    if self.orientation == Qt.Vertical:
        return end - (end - start) * value / 1000
    return None + (end - start) * value / 1000


def _value(self, coordinate):
    (start, end) = self._track()
    if self.orientation == Qt.Vertical:
        value = ((end - coordinate) / (end - start)) * 1000
    else:
        value = ((coordinate - start) / (end - start)) * 1000
    return int(np.clip(round(value), 0, 1000))


def paintEvent(self, event):
