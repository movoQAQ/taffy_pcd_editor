def RegionDeleteWorker():
    __module__ = __name__
    __qualname__ = 'RegionDeleteWorker'
    completed = pyqtSignal(int, object, int)
    failed = pyqtSignal(int, str)
    
    
    def __init__(self, request_id, points, equations, bounds, visible_ranges):
        nonlocal __class__
        super().__init__()
        self.request_id = request_id
        self.points = points
        self.equations = equations.copy()
        """original function name <genexpr> is illegal, use a temp name."""
    
        def __temp_5176(comp_arg_0):
            for __temp_5177 in comp_arg_0:
                bound = __temp_5177
                yield bound.copy()
                continue
            return None
        self.bounds = tuple(__temp_5176(iter(bounds)))
        self.visible_ranges = visible_ranges.copy()
        return None
    
    
    def run(self):
        try:
            remove = points_inside_region(self.points, self.equations, self.
                bounds, self.visible_ranges)
            removed = int(np.count_nonzero(remove))
            if removed:
                if removed < len(self.points):
                    available = available_memory_bytes()
                    if available:
                        if (len(self.points) - removed) * 12 > available * 0.75:
                            raise MemoryError('删除结果超出安全内存预算，请先释放内存后重试。')
                    self.completed.emit(self.request_id, self.points[~remove],
                        removed)
                    return None
            self.completed.emit(self.request_id, None, removed)
        finally:
            return None
    
    
    __classcell__ = __class__
    return __class__
