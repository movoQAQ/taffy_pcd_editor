# Source Generated with Decompyle++
# File: 138.pyc (Python 3.10)

if request_id != self.filter_request_id:
    return None
filtered_full = None
self.completion_base_points = None
self.completion_markers.clear()
layer = self._find_layer(self.active_layer_id)
if layer is not None:
    layer['edit_points'] = filtered_full
self._replace_active_source_points(filtered_full)
self.filter_status.setText('滤波结果已写回完整点云；范围外的原始点保持不变。')
self.render_count.setText(f'''当前范围处理 {fmt_number(len(points))} 个原始点 · 渲染 {fmt_number(len(self.points))} 点''')
self.vtk_widget.GetRenderWindow().Render()
if self.write_filtered.isChecked():
    (path, _) = QFileDialog.getSaveFileName(self, '另存滤波点云', 'filtered_view.pcd', 'PCD 点云 (*.pcd)')
    if path:
        self._start_write(path, filtered_full)
self.show_filter_result_popup(True)
