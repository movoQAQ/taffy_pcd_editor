def cancel_point_edit_mode(self):
    self.point_edit_mode = None
    self.region_pick_scope = None
    self._set_point_pick_mode(False)
    self._clear_region_markers()
    self.region_pick_status.setText('点选模式已取消。')
    return None
