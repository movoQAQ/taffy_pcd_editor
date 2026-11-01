def _fail_full_point_load_for_delete(self, request_id, error):
    self.edit_load_worker = None
    self.delete_region_button.setEnabled(True)
    if request_id == self.edit_load_request:
        self.region_pick_status.setText('完整点云读取失败：' + str(error))
        QMessageBox.warning(self, '完整点云读取失败', error)
        return None
    return None
