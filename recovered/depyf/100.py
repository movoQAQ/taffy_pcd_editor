def _picked_visible_point(self, x, y):
    point_id = self._picked_render_point_id(x, y)
    if point_id < 0:
        return None
    point = self.points[point_id].copy()
    scope = self.axis_ranges
    """original function name <genexpr> is illegal, use a temp name."""
    
    
    def __temp_6623(comp_arg_0):
        nonlocal point, scope
        for __temp_6624 in comp_arg_0:
            __temp_6625, __temp_6626 = __temp_6624
            i = __temp_6625
            axis = __temp_6626
            if scope[axis][0] <= point[i]:
                yield point[i] <= scope[axis][1]
            else:
                yield scope[axis][0] <= point[i]
            continue
        return None
    
    
    if not all(__temp_6623(iter(enumerate(('x', 'y', 'z'))))):
        return None
    return point
