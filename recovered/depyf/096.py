def _on_embedded_double_click(self, x, y):
    if self.point_edit_mode == 'delete':
        self._pick_delete_at_screen(x, y)
        return None
    return None
