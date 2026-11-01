# Source Generated with Decompyle++
# File: 118.pyc (Python 3.10)

self.region_delete_worker = None
self.delete_region_button.setEnabled(True)
if request_id == self.region_delete_request:
    self.region_pick_status.setText(f'''删除失败：{error}''')
    QMessageBox.warning(self, '删除失败', error)
    return None
