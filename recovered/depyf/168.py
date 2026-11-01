def apply_axis_range(self, axis, low, high):
    if self.points is None:
        return None
    __temp_7404, __temp_7405 = self.axis_bounds[axis]
    min_value = __temp_7404
    max_value = __temp_7405
    span = max_value - min_value
    low_value = min_value + span * low / 1000
    high_value = min_value + span * high / 1000
    self.axis_ranges[axis] = low_value, high_value
    planes = {x: (self.x_low_plane, self.x_high_plane, 0), y: (self.y_low_plane,
        self.y_high_plane, 1), z: (self.low_plane, self.high_plane, 2)}
    __temp_7407, __temp_7408, __temp_7409 = planes[axis]
    low_plane = __temp_7407
    high_plane = __temp_7408
    dimension = __temp_7409
    origin_low = [0.0] * 3
    origin_high = [0.0] * 3
    origin_low[dimension] = low_value
    origin_high[dimension] = high_value
    low_plane.SetOrigin(*origin_low)
    high_plane.SetOrigin(*origin_high)
    getattr(self, str(axis) + '_overlay_low').setText(format(low_value, '.1f') +
        ' m')
    getattr(self, str(axis) + '_overlay_high').setText(format(high_value, '.1f'
        ) + ' m')
    self.visible_stats_timer.start()
    self.vtk_widget.GetRenderWindow().Render()
    return None
