def TaffyPatternFrame():
    __module__ = __name__
    __qualname__ = 'TaffyPatternFrame'
    __doc__ = 'A very light cat-ear and star pattern used behind tool controls.'
    
    
    def paintEvent(self, event):
        nonlocal __class__
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(QColor(217, 97, 150, 28), 1.2))
        painter.setBrush(Qt.NoBrush)
        for __temp_4845 in iter(enumerate(range(22, self.height() + 55, 72))):
            __temp_4846, __temp_4847 = __temp_4845
            row = __temp_4846
            y = __temp_4847
            if row % 2:
                offset = 16
            else:
                offset = 58
            for __temp_4850 in iter(range(offset, self.width() + 55, 94)):
                x = __temp_4850
                painter.drawEllipse(x, y + 7, 12, 10)
                painter.drawPolyline(QPolygon([QPoint(x + 1, y + 9), QPoint(x +
                    4, y), QPoint(x + 7, y + 8)]))
                painter.drawPolyline(QPolygon([QPoint(x + 6, y + 8), QPoint(x +
                    10, y), QPoint(x + 12, y + 9)]))
                painter.drawLine(x + 22, y + 7, x + 28, y + 7)
                painter.drawLine(x + 25, y + 4, x + 25, y + 10)
                painter.drawEllipse(x + 43, y + 4, 3, 3)
                continue
            continue
        return None
    
    
    __classcell__ = __class__
    return __class__
