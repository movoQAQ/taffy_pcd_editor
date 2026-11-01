def _fail_full_load(self, request_id, layer_id, error):
    if layer_id == self.active_layer_id:
        self.filter_status.setText('完整点云载入失败：' + str(error))
        QMessageBox.warning(self, '完整点云载入失败', str(error))
        return None
    return None
