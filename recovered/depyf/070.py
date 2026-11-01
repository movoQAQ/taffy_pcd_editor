def _start_write(self, path, points, source_path):
    """original function name <lambda> is illegal, use a temp name."""
    
    
    def __temp_5883():
        nonlocal path, points, source_path
        return write_full_pcd(path, points=points, source_path=source_path)
    
    
    worker = CloudTaskWorker(__temp_5883)
    """original function name <lambda> is illegal, use a temp name."""
    
    
    def __temp_5886(written):
        nonlocal self
        return self.filter_status.setText('已写入：' + str(Path(written).name))
    
    
    worker.completed.connect(__temp_5886)
    """original function name <lambda> is illegal, use a temp name."""
    
    
    def __temp_5890(error):
        nonlocal self
        return QMessageBox.warning(self, '写入失败', error)
    
    
    worker.failed.connect(__temp_5890)
    self._track_worker(worker)
    self.filter_status.setText('正在后台写入 PCD…')
    worker.start()
    return None
