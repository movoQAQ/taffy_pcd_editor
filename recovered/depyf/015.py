def _track(self):
    if self.orientation == Qt.Vertical:
        extent = self.height()
    else:
        extent = self.width()
    start = 12
    end = extent - 12
    return start, max(start + 1, end)
