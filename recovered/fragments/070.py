# Source Generated with Decompyle++
# File: 070.pyc (Python 3.10)

worker = None((lambda : write_full_pcd(path, points, source_path, **('points', 'source_path'))))
None((lambda written = None: self.filter_status.setText(f'''已写入：{Path(written).name}''')))
None((lambda error = None: QMessageBox.warning(self, '写入失败', error)))
self._track_worker(worker)
self.filter_status.setText('正在后台写入 PCD…')
worker.start()
