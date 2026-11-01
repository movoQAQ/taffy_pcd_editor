def _finish_full_point_load_for_delete(self, request_id, points):
    self.edit_load_worker = None
    self.delete_region_button.setEnabled(True)
    if not request_id != self.edit_load_request:
        if self.edit_load_layer_id != self.active_layer_id:
            return None
    else:
        return None
    layer = self._find_layer(self.active_layer_id)
    if layer is None:
        return None
    layer['edit_points'] = points
    self.region_pick_status.setText('完整点云已载入：' + str(fmt_number(len(points))) +
        ' 点，正在删除…')
    self._delete_region_from_points(points)
    return None
