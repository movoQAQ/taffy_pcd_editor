def run(self):
    try:
        remove = points_inside_region(self.points, self.equations, self.bounds,
            self.visible_ranges)
        removed = int(np.count_nonzero(remove))
        if removed:
            if removed < len(self.points):
                available = available_memory_bytes()
                if available:
                    if (len(self.points) - removed) * 12 > available * 0.75:
                        raise MemoryError('删除结果超出安全内存预算，请先释放内存后重试。')
                self.completed.emit(self.request_id, self.points[~remove], removed)
                return None
        self.completed.emit(self.request_id, None, removed)
    finally:
        return None
