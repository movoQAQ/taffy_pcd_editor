# Source Generated with Decompyle++
# File: 140.pyc (Python 3.10)

if self.filter_result_popup is not None:
    self.filter_result_popup.close()
popup = QMessageBox(self)
popup.setWindowTitle('滤波完成' if success else '滤波失败')
popup.setText('滤波成功喵' if success else '滤波失败喵')
popup.setIcon(QMessageBox.Information if success else QMessageBox.Warning)
popup.setStandardButtons(QMessageBox.Ok)
popup.setAttribute(Qt.WA_DeleteOnClose)
self.filter_result_popup = popup
None((lambda _result = None: setattr(self, 'filter_result_popup', None)))
popup.show()
close_timer = QTimer(popup)
close_timer.setSingleShot(True)
close_timer.timeout.connect(popup.accept)
close_timer.start(1900)
