# Source Generated with Decompyle++
# File: 169.pyc (Python 3.10)

if not self.render_source_points is None or self.total_points:
    return None
layer = None._find_layer(self.active_layer_id)
if layer is None or 'edit_points' not in layer:
    self.visible_count.setText('--')
    self.visible_percent.setText('完整点云加载中')
    return None
None.visible_count_request += 1
if self.visible_count_worker is not None and self.visible_count_worker.isRunning():
    self.visible_count_worker.requestInterruption()
    return None
request_id = None.visible_count_request
worker = VisibleCountWorker(request_id, layer['id'], layer['edit_points'], dict(self.axis_ranges))
worker.completed.connect(self._finish_visible_count)
None((lambda : self._visible_count_finished(worker)))
self._track_worker(worker)
self.visible_count_worker = worker
worker.start()
