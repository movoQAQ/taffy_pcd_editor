def _track_worker(self, worker):
    self.task_workers.add(worker)
    """original function name <lambda> is illegal, use a temp name."""
    
    
    def __temp_5871():
        nonlocal self, worker
        return self.task_workers.discard(worker)
    
    
    worker.finished.connect(__temp_5871)
    worker.finished.connect(worker.deleteLater)
    return None
