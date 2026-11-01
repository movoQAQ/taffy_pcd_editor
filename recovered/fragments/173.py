# Source Generated with Decompyle++
# File: 173.pyc (Python 3.10)

if self._editing_busy():
    QMessageBox.information(self, '任务运行中', '请等待当前后台任务完成后再导入新点云。')
    return None
(path, _) = None.getOpenFileName(self, '导入 PCD 点云', str(Path.home()), '点云文件 (*.pcd);;所有文件 (*)')
if not path:
    return None
(points, full_z, total) = load_pcd_data(path)
self.set_cloud(points, Path(path).stem, Path(path).name, full_z, total, path)
self.full_load_request += 1
request_id = self.full_load_request
layer_id = self.active_layer_id
self.filter_status.setText('显示抽样已加载；正在后台载入完整原始点云…')
worker = FullPointLoadWorker(request_id, path, True, **('include_bounds',))
None((lambda job = None, data = None, bounds = None, target = None: self._finish_full_load(job, target, data, bounds)))
None((lambda job = None, error = None, target = None: self._fail_full_load(job, target, error)))
None((lambda job = None: self.full_load_workers.pop(job, None)))
self._track_worker(worker)
None((lambda : if self.full_load_worker is worker:
setattr(self, 'full_load_worker', None)))
self.full_load_worker = worker
self.full_load_workers[request_id] = worker
worker.start()
:
    if self._editing_busy():
        QMessageBox.information(self, '任务运行中', '请等待当前后台任务完成后再导入新点云。')
        return None
    (path, _) = None.getOpenFileName(self, '导入 PCD 点云', str(Path.home()), '点云文件 (*.pcd);;所有文件 (*)')
    if not path:
        return None
    (points, full_z, total) = load_pcd_data(path)
    self.set_cloud(points, Path(path).stem, Path(path).name, full_z, total, path)
    self.full_load_request += 1
    request_id = self.full_load_request
    layer_id = self.active_layer_id
    self.filter_status.setText('显示抽样已加载；正在后台载入完整原始点云…')
    worker = FullPointLoadWorker(request_id, path, True, **('include_bounds',))
    None((lambda job = None, data = None, bounds = None, target = None: self._finish_full_load(job, target, data, bounds)))
    None((lambda job = None, error = None, target = None: self._fail_full_load(job, target, error)))
    None((lambda job = None: self.full_load_workers.pop(job, None)))
    self._track_worker(worker)
    None((lambda : if self.full_load_worker is worker:
setattr(self, 'full_load_worker', None)))
    self.full_load_worker = worker
    self.full_load_workers[request_id] = worker
    worker.start()
    
    return None
return None
# WARNING: Decompyle incomplete
