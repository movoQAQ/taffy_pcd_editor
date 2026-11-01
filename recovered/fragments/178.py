# Source Generated with Decompyle++
# File: 178.pyc (Python 3.10)

layer = self._find_layer(layer_id)
if layer is None:
    return None
layer['edit_points'] = None
(bounds_min, bounds_max) = bounds
layer['axis_bounds'] = (lambda .0 = None: pass# WARNING: Decompyle incomplete
)(enumerate(('x', 'y', 'z')))
layer['total_points'] = len(points)
if layer_id != self.active_layer_id:
    return None
self.axis_bounds = None(layer['axis_bounds'])
self.total_points = layer['total_points']
for axis in 'xyz':
    slider = getattr(self, f'''{axis}_range_slider''')
    (low, high) = self.axis_bounds[axis]
    self.axis_ranges[axis] = (low + (high - low) * slider.low / 1000, low + (high - low) * slider.high / 1000)
layer['axis_ranges'] = dict(self.axis_ranges)
(self.z_min, self.z_max) = self.axis_bounds['z']
self.mapper.SetScalarRange(self.z_min, self.z_max)
self.lookup.SetTableRange(self.z_min, self.z_max)
self._set_slider_extent()
for axis in 'xyz':
    slider = getattr(self, f'''{axis}_range_slider''')
    self.apply_axis_range(axis, slider.low, slider.high)
self.layer_points.setText(f'''{fmt_number(len(points))} 点   ·   视图抽样 {fmt_number(len(layer['source_points']))}''')
self.metric_points.setText(fmt_number(len(points)))
self.filter_status.setText('完整原始点云已载入；可执行滤波、删除和补全。')
