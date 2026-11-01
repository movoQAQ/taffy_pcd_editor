def _finish_full_load(self, request_id, layer_id, points, bounds):
    layer = self._find_layer(layer_id)
    if layer is None:
        return None
    layer['edit_points'] = points
    __temp_7477, __temp_7478 = bounds
    bounds_min = __temp_7477
    bounds_max = __temp_7478
    """original function name <dictcomp> is illegal, use a temp name."""
    
    
    def __temp_7479(comp_arg_0):
        nonlocal bounds_max, bounds_min
        __temp_7480 = {}
        for __temp_7481 in comp_arg_0:
            __temp_7482, __temp_7483 = __temp_7481
            i = __temp_7482
            axis = __temp_7483
            __temp_7480.__setitem__(axis, (float(bounds_min[i]), float(
                bounds_max[i])))
            continue
        return __temp_7480
    
    
    layer['axis_bounds'] = __temp_7479(iter(enumerate(('x', 'y', 'z'))))
    layer['total_points'] = len(points)
    if layer_id != self.active_layer_id:
        return None
    self.axis_bounds = dict(layer['axis_bounds'])
    self.total_points = layer['total_points']
    for __temp_7490 in iter('xyz'):
        axis = __temp_7490
        slider = getattr(self, str(axis) + '_range_slider')
        __temp_7492, __temp_7493 = self.axis_bounds[axis]
        low = __temp_7492
        high = __temp_7493
        self.axis_ranges[axis] = low + (high - low) * slider.low / 1000, low + (
            high - low) * slider.high / 1000
        continue
    layer['axis_ranges'] = dict(self.axis_ranges)
    __temp_7495, __temp_7496 = self.axis_bounds['z']
    self.z_min = __temp_7495
    self.z_max = __temp_7496
    self.mapper.SetScalarRange(self.z_min, self.z_max)
    self.lookup.SetTableRange(self.z_min, self.z_max)
    self._set_slider_extent()
    for __temp_7500 in iter('xyz'):
        axis = __temp_7500
        slider = getattr(self, str(axis) + '_range_slider')
        self.apply_axis_range(axis, slider.low, slider.high)
        continue
    self.layer_points.setText(str(fmt_number(len(points))) + ' 点   ·   视图抽样 ' +
        str(fmt_number(len(layer['source_points']))))
    self.metric_points.setText(fmt_number(len(points)))
    self.filter_status.setText('完整原始点云已载入；可执行滤波、删除和补全。')
    return None
