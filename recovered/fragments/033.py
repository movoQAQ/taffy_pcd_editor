# Source Generated with Decompyle++
# File: 033.pyc (Python 3.10)

doubleClicked = pyqtSignal()

def mouseDoubleClickEvent(self = None, event = None):
    if event.button() == Qt.LeftButton:
        self.doubleClicked.emit()
        event.accept()
        return None
    None().mouseDoubleClickEvent(event)

__classcell__ = None
