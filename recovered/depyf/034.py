def mouseDoubleClickEvent(self, event):
    nonlocal __class__
    if event.button() == Qt.LeftButton:
        self.doubleClicked.emit()
        event.accept()
        return None
    super().mouseDoubleClickEvent(event)
    return None
