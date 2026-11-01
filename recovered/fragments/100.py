# Source Generated with Decompyle++
# File: 100.pyc (Python 3.10)

point_id = self._picked_render_point_id(x, y)
if point_id < 0:
    return None
point = None.points[point_id].copy()
scope = self.axis_ranges
if not None((lambda .0 = None: for i, axis in .0:
None if point[i] <= point[i] else point[i] <= scope[axis][1])(enumerate(('x', 'y', 'z')))):
    return None
