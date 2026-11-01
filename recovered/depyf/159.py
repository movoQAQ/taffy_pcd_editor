def _write_layer(self, layer, path):
    if self._editing_busy():
        self.filter_status.setText('请等待后台任务完成后再保存或导出。')
        return None
    if 'edit_points' in layer:
        self._start_write(path, points=layer['edit_points'])
        return None
    if layer.get('source_path'):
        if Path(layer['source_path']).is_file():
            self._start_write(path, source_path=layer['source_path'])
            return None
    QMessageBox.warning(self, '写入失败', '没有完整原始点云，已取消写入，避免保存抽样数据。')
    return None
