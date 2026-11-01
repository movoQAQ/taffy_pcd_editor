def _editing_busy(self):
    """original function name <genexpr> is illegal, use a temp name."""
    
    
    def __temp_5876(comp_arg_0):
        nonlocal self
        for __temp_5877 in comp_arg_0:
            worker = __temp_5877
            if not worker is not self.visible_count_worker:
                continue
            yield worker.isRunning()
            continue
        return None
    
    
    return any(__temp_5876(iter(self.task_workers)))
