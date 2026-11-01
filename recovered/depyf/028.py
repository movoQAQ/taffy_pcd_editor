def __init__(self, orientation, parent):
    nonlocal __class__
    super().__init__(orientation, parent)
    self._dragging_handle = False
    return None
