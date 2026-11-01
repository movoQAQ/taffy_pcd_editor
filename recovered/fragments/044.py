# Source Generated with Decompyle++
# File: 044.pyc (Python 3.10)

result = np.ones(len(points), bool, **('dtype',))
for start in range(0, len(points), 1000000):
    chunk = points[start:start + 1000000]
    inside = result[start:start + len(chunk)]
    for column, axis in enumerate('xyz'):
        (low, high) = ranges[axis]
        inside &= (chunk[(:, column)] >= low) & (chunk[(:, column)] <= high)
return result
