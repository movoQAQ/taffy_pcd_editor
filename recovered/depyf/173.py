def open_file(self):
    if self._editing_busy():
        QMessageBox.information(self, '任务运行中', '请等待当前后台任务完成后再导入新点云。')
        return None
    __temp_7447, __temp_7448 = QFileDialog.getOpenFileName(self, '导入 PCD 点云',
        str(Path.home()), '点云文件 (*.pcd);;所有文件 (*)')
    path = __temp_7447
    _ = __temp_7448
    if not path:
        return None
    try:
        __temp_7450, __temp_7451, __temp_7452 = load_pcd_data(path)
        points = __temp_7450
        full_z = __temp_7451
        total = __temp_7452
        self.set_cloud(points, Path(path).stem, Path(path).name, full_z, total,
            path)
        self.full_load_request += 1
        self.full_load_request = self.full_load_request
        request_id = self.full_load_request
        layer_id = self.active_layer_id
        self.filter_status.setText('显示抽样已加载；正在后台载入完整原始点云…')
        worker = FullPointLoadWorker(request_id, path, include_bounds=True)
        """original function name <lambda> is illegal, use a temp name."""
    
        def __temp_7458(job, data, bounds, target):
            nonlocal self
            return self._finish_full_load(job, target, data, bounds)
        worker.loaded_with_bounds.connect(__temp_7458)
        """original function name <lambda> is illegal, use a temp name."""
    
        def __temp_7461(job, error, target):
            nonlocal self
            return self._fail_full_load(job, target, error)
        worker.failed.connect(__temp_7461)
        """original function name <lambda> is illegal, use a temp name."""
    
        def __temp_7464(job):
            nonlocal self
            return self.full_load_workers.pop(job, None)
        worker.finished.connect(__temp_7464)
        self._track_worker(worker)
        """original function name <lambda> is illegal, use a temp name."""
    
        def __temp_7468():
            nonlocal self, worker
            if self.full_load_worker is worker:
                return setattr(self, 'full_load_worker', None)
            return None
        worker.finished.connect(__temp_7468)
        self.full_load_worker = worker
        self.full_load_workers[request_id] = worker
        worker.start()
    finally:
        return None
