def _pick_completion_at_screen(self, x, y):
    if self.point_edit_mode != 'completion':
        return None
    point = self._picked_visible_point(x, y)
    if point is None:
        self.region_pick_status.setText('没有命中点云，请双击点云点位。')
        return None
    self.complete_cloud_at(point)
    return None
