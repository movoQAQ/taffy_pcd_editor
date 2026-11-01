# Source Generated with Decompyle++
# File: 134.pyc (Python 3.10)

if not self.filter_enabled.isChecked():
    self.filter_status.setText('请先开启温和滤波。')
    return None
None.filter_request_id += 1
self.filter_recalculate_requested = True
self.filter_debounce.stop()
self.start_display_filter()
