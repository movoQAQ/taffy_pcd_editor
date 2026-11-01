# Source Generated with Decompyle++
# File: 037.pyc (Python 3.10)

if event.button() == Qt.LeftButton and getattr(self, '_point_pick_mode', False):
    (render_width, render_height) = self.GetRenderWindow().GetSize()
    if render_width > 0 and render_height > 0:
        x = round(event.x() * render_width / self.width())
        y = round((self.height() - event.y() - 1) * render_height / self.height())
        self.doubleClicked.emit(x, y)
super().mousePressEvent(event)
