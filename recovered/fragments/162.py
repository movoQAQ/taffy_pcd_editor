# Source Generated with Decompyle++
# File: 162.pyc (Python 3.10)

layer = self._find_layer(layer_id)
if layer is None:
    return None
if None != self.active_layer_id and self._editing_busy():
    self.filter_status.setText('后台任务运行中，完成后可切换编辑图层。')
    return None
previous = self._find_layer(self.active_layer_id) if None.active_layer_id is not None else None
if previous is not layer:
    self.point_edit_mode = None
    self.region_pick_points.clear()
    self.region_pick_scope = None
    self.selected_hull_equations = None
    self.selected_region_vertices = None
    self._clear_region_markers()
    self.completion_base_points = None
    self.completion_markers.clear()
    self._set_point_pick_mode(False)
if previous is not None:
    previous['display_points'] = self.points.copy()
    previous['axis_ranges'] = dict(self.axis_ranges)
    previous['mapper'].RemoveAllClippingPlanes()
self.filter_request_id += 1
self.active_layer_id = layer_id
self.points_actor = layer['actor']
self.mapper = layer['mapper']
self.render_source_points = layer['source_points']
self.full_z = layer['full_z']
self.total_points = layer['total_points']
(self.z_min, self.z_max) = layer['axis_bounds']['z']
if self.z_max - self.z_min < 1e-06:
    self.z_max = self.z_min + 0.001
self.axis_bounds = dict(layer['axis_bounds'])
self.axis_ranges = dict(layer['axis_ranges'])
self.mapper.SetLookupTable(self.lookup)
self.mapper.SetScalarRange(self.z_min, self.z_max)
self.mapper.RemoveAllClippingPlanes()
self.lookup.SetTableRange(self.z_min, self.z_max)
# WARNING: Decompyle incomplete
