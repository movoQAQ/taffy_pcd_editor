def __init__(self, orientation, parent):
    nonlocal __class__
    super().__init__(parent)
    self.orientation = orientation
    self.setStyleSheet(
        'background:#fff8fd;border:1px solid #eaddea;border-radius:8px;')
    self.setFocusPolicy(Qt.StrongFocus)
    self.low = 0
    self.high = 1000
    self.dragging = None
    if orientation == Qt.Vertical:
        self.setFixedWidth(32)
        self.setMinimumHeight(140)
        return None
    self.setFixedHeight(32)
    self.setMinimumWidth(180)
    return None
