def toggle_fullscreen(self):
    if self.isFullScreen():
        self.showNormal()
        return None
    self.showFullScreen()
    return None
