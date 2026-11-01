# Source Generated with Decompyle++
# File: 113.pyc (Python 3.10)

self.edit_load_worker = None
self.delete_region_button.setEnabled(True)
if request_id != self.edit_load_request or self.edit_load_layer_id != self.active_layer_id:
    return None
layer = None._find_layer(self.active_layer_id)
if layer is None:
    return None
layer['edit_points'] = None
self.region_pick_status.setText(f'''完整点云已载入：{fmt_number(len(points))} 点，正在删除…''')
self._delete_region_from_points(points)
