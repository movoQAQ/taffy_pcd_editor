# Source Generated with Decompyle++
# File: 115.pyc (Python 3.10)

equations = self.selected_hull_equations
vertices = self.selected_region_vertices
if equations is None or vertices is None:
    return None
None.region_delete_request += 1
request_id = self.region_delete_request
self.region_delete_layer_id = self.active_layer_id
self.region_delete_equations = equations.copy()
self.region_delete_bounds = (vertices.min(0, **('axis',)), vertices.max(0, **('axis',)))
self.region_delete_expand_m = self.filter_parameter_sliders['region_expand'][0].value() / 100
visible_ranges = None((lambda .0 = None: [ self.axis_ranges[axis] for axis in .0 ])('xyz'), np.float64, **('dtype',))
worker = RegionDeleteWorker(request_id, points, equations, self.region_delete_bounds, visible_ranges)
worker.completed.connect(self._finish_region_delete)
worker.failed.connect(self._fail_region_delete)
self._track_worker(worker)
self.region_delete_worker = worker
self.delete_region_button.setEnabled(False)
self.region_pick_status.setText(f'''正在后台删除 {fmt_number(len(points))} 点中的选定区域…''')
worker.start()
