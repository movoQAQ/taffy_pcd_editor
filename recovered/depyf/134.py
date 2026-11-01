def recalculate_display_filter(self):
    if not self.filter_enabled.isChecked():
        self.filter_status.setText('请先开启温和滤波。')
        return None
    self.filter_request_id += 1
    self.filter_request_id = self.filter_request_id
    self.filter_recalculate_requested = True
    self.filter_debounce.stop()
    self.start_display_filter()
    return None
