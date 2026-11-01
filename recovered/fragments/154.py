# Source Generated with Decompyle++
# File: 154.pyc (Python 3.10)

menu = QMenu(self)
export_action = menu.addAction('导出当前图层 PCD…')
save_action = menu.addAction('保存原始 PCD…')
selected = menu.exec_(button.mapToGlobal(QPoint(button.width(), 0)))
if selected == export_action:
    self.export_layer(layer_id)
    return None
if None == save_action:
    self.save_layer_source(layer_id)
    return None
