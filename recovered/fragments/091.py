# Source Generated with Decompyle++
# File: 091.pyc (Python 3.10)

if self.completion_base_points is None:
    self.region_pick_status.setText('当前没有本轮放置的补全点。')
    return None
self.point_edit_mode = None
self._set_point_pick_mode(False)
self._replace_active_source_points(self.completion_base_points)
self.completion_base_points = None
self.completion_markers.clear()
self.region_pick_status.setText('已清空本轮放置的补全点。')
