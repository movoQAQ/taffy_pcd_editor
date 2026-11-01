def _set_slider_extent(self):
    for __temp_7388 in iter((('x', self.x_range_slider), ('y', self.
        y_range_slider), ('z', self.z_range_slider))):
        __temp_7389, __temp_7390 = __temp_7388
        axis = __temp_7389
        slider = __temp_7390
        __temp_7391, __temp_7392 = self.axis_bounds[axis]
        low = __temp_7391
        high = __temp_7392
        span = max(high - low, 1e-09)
        __temp_7394, __temp_7395 = self.axis_ranges[axis]
        selected_low = __temp_7394
        selected_high = __temp_7395
        slider.set_range(round((selected_low - low) / span * 1000), round((
            selected_high - low) / span * 1000))
        suffix = ' m'
        getattr(self, str(axis) + '_overlay_low').setText(format(low, '.1f') +
            str(suffix))
        getattr(self, str(axis) + '_overlay_high').setText(format(high, '.1f') +
            str(suffix))
        continue
    return None
