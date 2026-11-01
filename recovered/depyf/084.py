def start_region_selection(self):
    self.selected_hull_equations = None
    self.selected_region_vertices = None
    self.region_pick_scope = dict(self.axis_ranges)
    self.pick_cache = None
    self._clear_region_preview()
    self.region_pick_points.clear()
    self._clear_region_markers()
    self.point_edit_mode = 'delete'
    self._set_point_pick_mode(True)
    self.region_pick_status.setText('双击选择区域顶点，至少 4 个不共面的点；然后点击“计算凸包区域”。')
    return None
