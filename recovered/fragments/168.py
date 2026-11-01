# Source Generated with Decompyle++
# File: 168.pyc (Python 3.10)

if self.points is None:
    return None
(min_value, max_value) = None.axis_bounds[axis]
span = max_value - min_value
low_value = min_value + span * low / 1000
high_value = min_value + span * high / 1000
self.axis_ranges[axis] = (low_value, high_value)
planes = {
    'x': (self.x_low_plane, self.x_high_plane, 0),
    'y': (self.y_low_plane, self.y_high_plane, 1),
    'z': (self.low_plane, self.high_plane, 2) }
(low_plane, high_plane, dimension) = planes[axis]
origin_low = [
    0.0] * 3
origin_high = [
    0.0] * 3
origin_low[dimension] = low_value
origin_high[dimension] = high_value
# WARNING: Decompyle incomplete
