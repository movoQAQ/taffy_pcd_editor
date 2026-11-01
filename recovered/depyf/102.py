def _pick_delete_at_screen(self, x, y):
    if self.point_edit_mode != 'delete':
        return None
    point = self._picked_visible_point(x, y)
    if point is None:
        self.region_pick_status.setText('未选中可见点，请靠近点云双击。')
        return None
    self.region_pick_points.append(point)
    self._add_region_marker(point)
    self.selected_hull_equations = None
    self.region_pick_status.setText('已选 ' + str(len(self.region_pick_points)) +
        ' 个区域顶点；点击“计算凸包区域”。')
    return None
