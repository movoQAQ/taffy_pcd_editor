# Source Generated with Decompyle++
# File: 117.pyc (Python 3.10)

self.region_delete_worker = None
self.delete_region_button.setEnabled(True)
if request_id != self.region_delete_request or self.region_delete_layer_id != self.active_layer_id:
    return None
if not None:
    QMessageBox.information(self, '没有匹配点', '所选立体区域内没有可删除的点。')
    return None
if None is None:
    QMessageBox.warning(self, '无法删除', '该区域包含图层全部点，至少保留一个点。')
    return None
None._replace_active_source_points(remaining_points)
if self.completion_base_points is not None:
    self.completion_base_points = None
self.completion_markers.clear()
self._clear_region_markers()
self.region_pick_status.setText(f'''已删除 {fmt_number(removed)} 个点（XYZ 各方向外扩 {self.region_delete_expand_m * 100:.0f} cm）。''')
