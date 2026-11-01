# Source Generated with Decompyle++
# File: 056.pyc (Python 3.10)

(low, high) = bounds
if visible_ranges is not None:
    low = np.maximum(low, visible_ranges[(:, 0)])
    high = np.minimum(high, visible_ranges[(:, 1)])
result = np.zeros(len(points), bool, **('dtype',))
if np.any(low > high):
    return result
for start in None(0, len(points), 250000):
    chunk = points[start:start + 250000]
    candidates = np.flatnonzero(np.all((chunk >= low) & (chunk <= high), 1, **('axis',)))
    if len(candidates):
        subset = chunk[candidates]
        result[start + candidates] = np.all((subset @ equations[(:, :3)].T) + equations[(:, 3)] <= 1e-06, 1, **('axis',))
return result
