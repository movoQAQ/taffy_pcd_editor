# Source Generated with Decompyle++
# File: 090.pyc (Python 3.10)

layer = self._find_layer(self.active_layer_id)
if layer is None:
    return np.empty((0, 3), np.float32, **('dtype',))
if None in layer:
    return layer['edit_points']
if None(layer['source_points']) >= layer['total_points']:
    layer['edit_points'] = layer['source_points']
    return layer['edit_points']
source_path = None.get('source_path')
if not source_path or Path(source_path).is_file():
    QMessageBox.warning(self, '无法载入完整点云', '原始 PCD 文件不可用，当前只能显示抽样点，无法安全编辑。')
    return layer['source_points']
None.setOverrideCursor(Qt.WaitCursor)
# WARNING: Decompyle incomplete
