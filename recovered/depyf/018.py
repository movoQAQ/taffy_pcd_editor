def paintEvent(self, event):
    painter = QPainter(self)
    painter.setRenderHint(QPainter.Antialiasing)
    __temp_4656, __temp_4657 = self._track()
    start = __temp_4656
    end = __temp_4657
    if self.orientation == Qt.Vertical:
        center = self.width() // 2
        """original function name <lambda> is illegal, use a temp name."""
    
        def point(value):
            nonlocal center, self
            return center, round(self._y(value))
    else:
        center = self.height() // 2
        """original function name <lambda> is illegal, use a temp name."""
    
        def point(value):
            nonlocal center, self
            return round(self._y(value)), center
    a = point(0)
    b = point(1000)
    painter.setPen(QPen(QColor('#c9b8cc'), 6, Qt.SolidLine, Qt.RoundCap))
    __temp_4668 = []
    __temp_4668.extend(a)
    __temp_4669 = __temp_4668
    __temp_4669.extend(b)
    painter.drawLine(*tuple(__temp_4669))
    painter.setPen(QPen(QColor('#d96196'), 3, Qt.SolidLine, Qt.RoundCap))
    __temp_4676 = []
    __temp_4676.extend(point(self.low))
    __temp_4678 = __temp_4676
    __temp_4678.extend(point(self.high))
    painter.drawLine(*tuple(__temp_4678))
    for __temp_4680 in iter((self.high, self.low)):
        value = __temp_4680
        painter.setPen(QPen(QColor('#d9a8bf'), 1))
        painter.setBrush(QColor('#ffffff'))
        __temp_4687, __temp_4688 = point(value)
        x = __temp_4687
        y = __temp_4688
        painter.drawEllipse(x - 6, y - 6, 12, 12)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor('#9d3b6c'))
        painter.drawEllipse(x - 3, y - 3, 6, 6)
        continue
    return None
