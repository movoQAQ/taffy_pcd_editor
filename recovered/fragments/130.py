# Source Generated with Decompyle++
# File: 130.pyc (Python 3.10)

layer = self._find_layer(self.active_layer_id) if self.active_layer_id is not None else None
if layer is None:
    return np.empty((0, 3), np.float32, **('dtype',))
if None not in layer:
    raise RuntimeError('当前图层没有可用的完整原始点云，已停止操作以避免处理抽样数据。')
return layer['edit_points']
