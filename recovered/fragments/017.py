# Source Generated with Decompyle++
# File: 017.pyc (Python 3.10)

(start, end) = self._track()
if self.orientation == Qt.Vertical:
    value = ((end - coordinate) / (end - start)) * 1000
else:
    value = ((coordinate - start) / (end - start)) * 1000
return int(np.clip(round(value), 0, 1000))
