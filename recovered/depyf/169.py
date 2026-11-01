def _update_visible_stats(self):
    if not self.render_source_points is None:
        if not self.total_points:
            return None
    else:
        return None
    layer = self._find_layer(self.active_layer_id)
    if not layer is None:
        if 'edit_points' not in layer:
            self.visible_count.setText('--')
            self.visible_percent.setText('完整点云加载中')
            return None
    else:
        self.visible_count.setText('--')
        self.visible_percent.setText('完整点云加载中')
        return None
    self.visible_count_request += 1
    self.visible_count_request = self.visible_count_request
    if self.visible_count_worker is not None:
        if self.visible_count_worker.isRunning():
            self.visible_count_worker.requestInterruption()
            return None
    request_id = self.visible_count_request
    worker = VisibleCountWorker(request_id, layer['id'], layer['edit_points'],
        dict(self.axis_ranges))
    worker.completed.connect(self._finish_visible_count)
    """original function name <lambda> is illegal, use a temp name."""
    
    
    def __temp_7431():
        nonlocal self, worker
        return self._visible_count_finished(worker)
    
    
    worker.finished.connect(__temp_7431)
    self._track_worker(worker)
    self.visible_count_worker = worker
    worker.start()
    return None
