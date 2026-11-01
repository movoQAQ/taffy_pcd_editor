def reset_range(self):
    for __temp_7521 in iter((('x', self.x_range_slider), ('y', self.
        y_range_slider), ('z', self.z_range_slider))):
        __temp_7522, __temp_7523 = __temp_7521
        axis = __temp_7522
        slider = __temp_7523
        slider.set_range(0, 1000)
        self.apply_axis_range(axis, 0, 1000)
        continue
    return None
