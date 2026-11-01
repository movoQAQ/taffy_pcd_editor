# Source Generated with Decompyle++
# File: 180.pyc (Python 3.10)

if layer_id == self.active_layer_id:
    self.filter_status.setText(f'''完整点云载入失败：{error}''')
    QMessageBox.warning(self, '完整点云载入失败', str(error))
    return None
