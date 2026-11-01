# Source Generated with Decompyle++
# File: 112.pyc (Python 3.10)

(points, count) = result
if layer_id != self.active_layer_id:
    return None
if None.completion_base_points is None:
    self.completion_base_points = base
self._replace_active_source_points(points)
self.region_pick_status.setText(f'''已补全 {fmt_number(count)} 个点，间距约 {spacing:.2f} m。''')
