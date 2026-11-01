# Source Generated with Decompyle++
# File: 039.pyc (Python 3.10)

'''A very light cat-ear and star pattern used behind tool controls.'''

def paintEvent(self = None, event = None):
    super().paintEvent(event)
    painter = QPainter(self)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setPen(QPen(QColor(217, 97, 150, 28), 1.2))
    painter.setBrush(Qt.NoBrush)
    for row, y in enumerate(range(22, self.height() + 55, 72)):
        offset = 16 if row % 2 else 58
        for x in range(offset, self.width() + 55, 94):
            painter.drawEllipse(x, y + 7, 12, 10)
            painter.drawPolyline(QPolygon([
                QPoint(x + 1, y + 9),
                QPoint(x + 4, y),
                QPoint(x + 7, y + 8)]))
            painter.drawPolyline(QPolygon([
                QPoint(x + 6, y + 8),
                QPoint(x + 10, y),
                QPoint(x + 12, y + 9)]))
            painter.drawLine(x + 22, y + 7, x + 28, y + 7)
            painter.drawLine(x + 25, y + 4, x + 25, y + 10)
            painter.drawEllipse(x + 43, y + 4, 3, 3)

__classcell__ = None
