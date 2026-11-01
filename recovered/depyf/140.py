def show_filter_result_popup(self, success):
    if self.filter_result_popup is not None:
        self.filter_result_popup.close()
        popup = QMessageBox(self)
    else:
        popup = QMessageBox(self)
    if success:
        popup.setWindowTitle('滤波完成')
    else:
        popup.setWindowTitle('滤波失败')
    if success:
        popup.setText('滤波成功喵')
    else:
        popup.setText('滤波失败喵')
    if success:
        popup.setIcon(QMessageBox.Information)
        popup.setStandardButtons(QMessageBox.Ok)
        popup.setAttribute(Qt.WA_DeleteOnClose)
        self.filter_result_popup = popup
    else:
        popup.setIcon(QMessageBox.Warning)
        popup.setStandardButtons(QMessageBox.Ok)
        popup.setAttribute(Qt.WA_DeleteOnClose)
        self.filter_result_popup = popup
    """original function name <lambda> is illegal, use a temp name."""
    
    
    def __temp_7007(_result):
        nonlocal self
        return setattr(self, 'filter_result_popup', None)
    
    
    popup.finished.connect(__temp_7007)
    popup.show()
    close_timer = QTimer(popup)
    close_timer.setSingleShot(True)
    close_timer.timeout.connect(popup.accept)
    close_timer.start(1900)
    return None
