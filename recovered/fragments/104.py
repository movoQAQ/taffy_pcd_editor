# Source Generated with Decompyle++
# File: 104.pyc (Python 3.10)

points = np.ascontiguousarray(points, np.float32, **('dtype',))
layer = self._find_layer(self.active_layer_id)
if not layer is None or len(points):
    return None
render_stride = None(1, int(np.ceil(len(points) / MAX_RENDER_POINTS)))
display_points = points[::render_stride].copy()
layer['source_points'] = display_points
layer['edit_points'] = points
layer['display_points'] = display_points
layer['total_points'] = len(points)
layer['full_z'] = display_points[(:, 2)]
layer['axis_ranges'] = dict(self.axis_ranges)
self.render_source_points = display_points
self.full_z = layer['full_z']
self.total_points = layer['total_points']
self.filter_request_id += 1
self.filter_enabled.blockSignals(True)
self.filter_enabled.setChecked(False)
self.filter_enabled.blockSignals(False)
self._set_render_points(display_points)
self._update_visible_stats()
self.render_count.setText(f'''渲染 {fmt_number(len(points))} 点''')
self.vtk_widget.GetRenderWindow().Render()
