def mouseReleaseEvent(self, event):
    nonlocal __class__
    if self._dragging_handle:
        super().mouseReleaseEvent(event)
        self._dragging_handle = False
    else:
        self._dragging_handle = False
    return None
