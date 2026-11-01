def _value(self, coordinate):
    __temp_4648, __temp_4649 = self._track()
    start = __temp_4648
    end = __temp_4649
    if self.orientation == Qt.Vertical:
        value = (end - coordinate) / (end - start) * 1000
    else:
        value = (coordinate - start) / (end - start) * 1000
    return int(np.clip(round(value), 0, 1000))
