def _y(self, value):
    __temp_4645, __temp_4646 = self._track()
    start = __temp_4645
    end = __temp_4646
    if self.orientation == Qt.Vertical:
        return end - (end - start) * value / 1000
    return start + (end - start) * value / 1000
