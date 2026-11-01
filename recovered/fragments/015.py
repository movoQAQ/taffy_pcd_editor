# Source Generated with Decompyle++
# File: 015.pyc (Python 3.10)

extent = self.height() if self.orientation == Qt.Vertical else self.width()
start = 12
end = extent - 12
return (start, max(start + 1, end))
