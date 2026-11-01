# Source Generated with Decompyle++
# File: 157.pyc (Python 3.10)

layer = self._find_layer(layer_id)
if layer is None:
    return None
suggested = f'''{None(layer['filename']).stem}_edited.pcd'''
(path, _) = QFileDialog.getSaveFileName(self, '导出当前图层点云', suggested, 'PCD 点云 (*.pcd)')
if not path:
    return None
None._write_layer(layer, path)
