def current_visible_source_points(self):
    if self.render_source_points is None:
        return np.empty((0, 3), dtype=np.float32)
    visible = np.ones(len(self.render_source_points), dtype=bool)
    for __temp_6909 in iter((('x', 0), ('y', 1), ('z', 2))):
        __temp_6910, __temp_6911 = __temp_6909
        axis = __temp_6910
        column = __temp_6911
        visible &= self.render_source_points[slice(None, None), column
            ] >= self.axis_ranges[axis][0]
        visible &= self.render_source_points[slice(None, None), column
            ] <= self.axis_ranges[axis][1]
        continue
    return self.render_source_points[visible]
