# Source Generated with Decompyle++
# File: 158.pyc (Python 3.10)

layer = self._find_layer(layer_id)
if layer is None:
    return None
suggested = None(layer['filename']).name
(path, _) = QFileDialog.getSaveFileName(self, '保存原始 PCD', suggested, 'PCD 点云 (*.pcd)')
if not path:
    return None
None._write_layer(layer, path)
