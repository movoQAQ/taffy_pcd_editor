def current_full_points(self):
    if self.active_layer_id is not None:
        layer = self._find_layer(self.active_layer_id)
    else:
        layer = None
    if layer is None:
        return np.empty((0, 3), dtype=np.float32)
    if 'edit_points' not in layer:
        raise RuntimeError('当前图层没有可用的完整原始点云，已停止操作以避免处理抽样数据。')
    return layer['edit_points']
