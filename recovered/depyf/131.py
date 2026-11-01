def current_visible_full_points(self, points):
    if points is None:
        points = self.current_full_points()
    if not len(points):
        return points
    visible = np.ones(len(points), dtype=bool)
    for __temp_6919 in iter((('x', 0), ('y', 1), ('z', 2))):
        __temp_6920, __temp_6921 = __temp_6919
        axis = __temp_6920
        column = __temp_6921
        __temp_6922, __temp_6923 = self.axis_ranges[axis]
        low = __temp_6922
        high = __temp_6923
        visible &= (points[slice(None, None), column] >= low) & (points[slice(
            None, None), column] <= high)
        continue
    return points[visible]
