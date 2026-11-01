def points_inside_region(points, equations, bounds, visible_ranges):
    __temp_5157, __temp_5158 = bounds
    low = __temp_5157
    high = __temp_5158
    if visible_ranges is not None:
        low = np.maximum(low, visible_ranges[slice(None, None), 0])
        high = np.minimum(high, visible_ranges[slice(None, None), 1])
    result = np.zeros(len(points), dtype=bool)
    if np.any(low > high):
        return result
    for __temp_5166 in iter(range(0, len(points), 250000)):
        start = __temp_5166
        chunk = points[slice(start, start + 250000)]
        candidates = np.flatnonzero(np.all((chunk >= low) & (chunk <= high),
            axis=1))
        if len(candidates):
            subset = chunk[candidates]
            result[start + candidates] = np.all(subset @ equations[slice(None,
                None), slice(None, 3)].T + equations[slice(None, None), 3] <= 
                1e-06, axis=1)
        continue
    return result
