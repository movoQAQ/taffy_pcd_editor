# Source Generated with Decompyle++
# File: 105.pyc (Python 3.10)

if self._editing_busy():
    self.region_pick_status.setText('后台任务运行中，请稍候再编辑。')
    return None
if None.selected_hull_equations is None:
    QMessageBox.warning(self, '区域尚未计算', '请先选至少 4 个不同且不共面的点，再点击“计算凸包区域”。')
    return None
if None(self.region_pick_points) < 4:
    QMessageBox.warning(self, '边界点不足', '删除区域至少需要 4 个点，请继续选点。')
    return None
layer = None._find_layer(self.active_layer_id)
if layer is None:
    return None
if None.full_load_worker is not None and self.full_load_worker.isRunning():
    self.region_pick_status.setText('完整原始点云仍在后台载入，请稍候。')
    return None
if None.region_delete_worker is not None and self.region_delete_worker.isRunning():
    return None
if None in layer:
    self._delete_region_from_points(layer['edit_points'])
    return None
if None(layer['source_points']) >= layer['total_points']:
    layer['edit_points'] = layer['source_points']
    self._delete_region_from_points(layer['edit_points'])
    return None
source_path = None.get('source_path')
if not source_path or Path(source_path).is_file():
    QMessageBox.warning(self, '无法载入完整点云', '原始 PCD 文件不可用，无法安全删除抽样之外的点。')
    return None
if None.edit_load_worker is not None and self.edit_load_worker.isRunning():
    return None
None.edit_load_request += 1
request_id = self.edit_load_request
self.edit_load_layer_id = layer['id']
self.region_pick_status.setText('正在后台读取完整点云以执行删除…')
self.delete_region_button.setEnabled(False)
worker = FullPointLoadWorker(request_id, source_path)
worker.loaded.connect(self._finish_full_point_load_for_delete)
worker.failed.connect(self._fail_full_point_load_for_delete)
self._track_worker(worker)
self.edit_load_worker = worker
worker.start()
