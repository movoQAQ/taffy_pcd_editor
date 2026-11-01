# Source Generated with Decompyle++
# File: 131.pyc (Python 3.10)

points = self.current_full_points() if points is None else points
if not len(points):
    return points
visible = None.ones(len(points), bool, **('dtype',))
for axis, column in (('x', 0), ('y', 1), ('z', 2)):
    (low, high) = self.axis_ranges[axis]
    visible &= (points[(:, column)] >= low) & (points[(:, column)] <= high)
return points[visible]
