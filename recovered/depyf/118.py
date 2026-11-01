def _fail_region_delete(self, request_id, error):
    self.region_delete_worker = None
    self.delete_region_button.setEnabled(True)
    if request_id == self.region_delete_request:
        self.region_pick_status.setText('删除失败：' + str(error))
        QMessageBox.warning(self, '删除失败', error)
        return None
    return None
