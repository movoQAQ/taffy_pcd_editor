# Source Generated with Decompyle++
# File: 119.pyc (Python 3.10)

remove = np.zeros(len(points), bool, **('dtype',))
for start in range(0, len(points), 250000):
    chunk = points[start:start + 250000]
    inside = np.all((chunk @ equations[(:, :3)].T) + equations[(:, 3)] <= 1e-06, 1, **('axis',))
    remove[start:start + len(chunk)] = inside
return points[~remove].copy()
