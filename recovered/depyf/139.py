def fail_display_filter(self, request_id, error):
    if request_id == self.filter_request_id:
        self.filter_status.setText('滤波未完成：' + str(error))
        self.show_filter_result_popup(False)
        return None
    return None
