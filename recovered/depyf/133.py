def schedule_display_filter(self):
    if self.render_source_points is None:
        return None
    self.filter_request_id += 1
    self.filter_request_id = self.filter_request_id
    if not self.filter_enabled.isChecked():
        return None
    self.filter_status.setText('参数已更改；点击重新计算处理当前 XYZ 范围内的完整原始点。')
    return None
