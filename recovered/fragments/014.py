# Source Generated with Decompyle++
# File: 014.pyc (Python 3.10)

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
