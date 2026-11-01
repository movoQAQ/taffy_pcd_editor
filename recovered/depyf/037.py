def mouseDoubleClickEvent(self, event):
    nonlocal __class__
    if event.button() == Qt.LeftButton:
        if getattr(self, '_point_pick_mode', False):
            __temp_4811, __temp_4812 = self.GetRenderWindow().GetSize()
            render_width = __temp_4811
            render_height = __temp_4812
            if render_width > 0:
                if render_height > 0:
                    x = round(event.x() * render_width / self.width())
                    y = round((self.height() - event.y() - 1) * render_height /
                        self.height())
                    self.doubleClicked.emit(x, y)
                    super().mousePressEvent(event)
                    return None
                else:
                    super().mousePressEvent(event)
                    return None
            else:
                super().mousePressEvent(event)
                return None
        else:
            super().mousePressEvent(event)
            return None
    else:
        super().mousePressEvent(event)
        return None
