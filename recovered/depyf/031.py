def mouseMoveEvent(self, event):
    nonlocal __class__
    if self._dragging_handle:
        super().mouseMoveEvent(event)
        return None
    event.ignore()
    return None
