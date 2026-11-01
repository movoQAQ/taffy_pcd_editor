def range_mask(points, ranges):
    result = np.ones(len(points), dtype=bool)
    for __temp_5044 in iter(range(0, len(points), 1000000)):
        start = __temp_5044
        chunk = points[slice(start, start + 1000000)]
        inside = result[slice(start, start + len(chunk))]
        for __temp_5047 in iter(enumerate('xyz')):
            __temp_5048, __temp_5049 = __temp_5047
            column = __temp_5048
            axis = __temp_5049
            __temp_5050, __temp_5051 = ranges[axis]
            low = __temp_5050
            high = __temp_5051
            inside &= (chunk[slice(None, None), column] >= low) & (chunk[slice(
                None, None), column] <= high)
            continue
        continue
    return result
