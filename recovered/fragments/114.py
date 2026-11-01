# Source Generated with Decompyle++
# File: 114.pyc (Python 3.10)

self.edit_load_worker = None
self.delete_region_button.setEnabled(True)
if request_id == self.edit_load_request:
    self.region_pick_status.setText(f'''完整点云读取失败：{error}''')
    QMessageBox.warning(self, '完整点云读取失败', error)
    return None
