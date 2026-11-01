def _finish_region_delete(self, request_id, remaining_points, removed):
    self.region_delete_worker = None
    self.delete_region_button.setEnabled(True)
    if not request_id != self.region_delete_request:
        if self.region_delete_layer_id != self.active_layer_id:
            return None
    else:
        return None
    if not removed:
        QMessageBox.information(self, '没有匹配点', '所选立体区域内没有可删除的点。')
        return None
    if remaining_points is None:
        QMessageBox.warning(self, '无法删除', '该区域包含图层全部点，至少保留一个点。')
        return None
    self._replace_active_source_points(remaining_points)
    if self.completion_base_points is not None:
        self.completion_base_points = None
    self.completion_markers.clear()
    self._clear_region_markers()
    self.region_pick_status.setText('已删除 ' + str(fmt_number(removed)) +
        ' 个点（XYZ 各方向外扩 ' + format(self.region_delete_expand_m * 100, '.0f') +
        ' cm）。')
    return None
