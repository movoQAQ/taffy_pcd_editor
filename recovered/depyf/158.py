def save_layer_source(self, layer_id):
    layer = self._find_layer(layer_id)
    if layer is None:
        return None
    suggested = Path(layer['filename']).name
    __temp_7211, __temp_7212 = QFileDialog.getSaveFileName(self, '保存原始 PCD',
        suggested, 'PCD 点云 (*.pcd)')
    path = __temp_7211
    _ = __temp_7212
    if not path:
        return None
    self._write_layer(layer, path)
    return None
