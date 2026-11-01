# Source Generated with Decompyle++
# File: 159.pyc (Python 3.10)

if self._editing_busy():
    self.filter_status.setText('请等待后台任务完成后再保存或导出。')
    return None
if None in layer:
    self._start_write(path, layer['edit_points'], **('points',))
    return None
if None.get('source_path') and Path(layer['source_path']).is_file():
    self._start_write(path, layer['source_path'], **('source_path',))
    return None
None.warning(self, '写入失败', '没有完整原始点云，已取消写入，避免保存抽样数据。')
