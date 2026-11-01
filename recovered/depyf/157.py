def export_layer(self, layer_id):
    layer = self._find_layer(layer_id)
    if layer is None:
        return None
    suggested = str(Path(layer['filename']).stem) + '_edited.pcd'
    __temp_7205, __temp_7206 = QFileDialog.getSaveFileName(self, '导出当前图层点云',
        suggested, 'PCD 点云 (*.pcd)')
    path = __temp_7205
    _ = __temp_7206
    if not path:
        return None
    self._write_layer(layer, path)
    return None
