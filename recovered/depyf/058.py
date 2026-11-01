def __init__(self, request_id, points, equations, bounds, visible_ranges):
    nonlocal __class__
    super().__init__()
    self.request_id = request_id
    self.points = points
    self.equations = equations.copy()
    """original function name <genexpr> is illegal, use a temp name."""
    
    
    def __temp_5194(comp_arg_0):
        for __temp_5195 in comp_arg_0:
            bound = __temp_5195
            yield bound.copy()
            continue
        return None
    
    
    self.bounds = tuple(__temp_5194(iter(bounds)))
    self.visible_ranges = visible_ranges.copy()
    return None
