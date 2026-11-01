def eventFilter(self, watched, event):
    nonlocal __class__
    if watched.objectName() == 'header':
        if event.type() == QEvent.MouseButtonPress:
            if event.button() == Qt.LeftButton:
                self._window_drag_offset = event.globalPos() - self.frameGeometry(
                    ).topLeft()
                return True
        if event.type() == QEvent.MouseMove:
            if self._window_drag_offset is not None:
                if event.buttons() & Qt.LeftButton:
                    self.move(event.globalPos() - self._window_drag_offset)
                    return True
        if event.type() == QEvent.MouseButtonRelease:
            self._window_drag_offset = None
            return True
    return super().eventFilter(watched, event)
