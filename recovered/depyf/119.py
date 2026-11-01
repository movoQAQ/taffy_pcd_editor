def _remove_points_in_hull(points, equations):
    remove = np.zeros(len(points), dtype=bool)
    for __temp_6781 in iter(range(0, len(points), 250000)):
        start = __temp_6781
        chunk = points[slice(start, start + 250000)]
        inside = np.all(chunk @ equations[slice(None, None), slice(None, 3)].T +
            equations[slice(None, None), 3] <= 1e-06, axis=1)
        remove[slice(start, start + len(chunk))] = inside
        continue
    return points[~remove].copy()
