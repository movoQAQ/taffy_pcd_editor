# Source Generated with Decompyle++
# File: 129.pyc (Python 3.10)

if self.render_source_points is None:
    return np.empty((0, 3), np.float32, **('dtype',))
visible = None.ones(len(self.render_source_points), bool, **('dtype',))
for axis, column in (('x', 0), ('y', 1), ('z', 2)):
    visible &= (self.render_source_points[(:, column)] >= self.axis_ranges[axis][0])
    visible &= (self.render_source_points[(:, column)] <= self.axis_ranges[axis][1])
return self.render_source_points[visible]
