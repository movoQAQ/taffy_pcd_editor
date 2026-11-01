def <lambda>(error):
    nonlocal self
    return QMessageBox.warning(self, '写入失败', error)
