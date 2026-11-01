def DisplayFilterWorker():
    __module__ = __name__
    __qualname__ = 'DisplayFilterWorker'
    completed = pyqtSignal(int, object)
    failed = pyqtSignal(int, str)
    
    
    def __init__(self, request_id, points, voxel_size, statistical,
        stat_neighbors, std_ratio, radius, radius_neighbors, radius_size,
        ranges, auto):
        nonlocal __class__
        super().__init__()
        self.request_id = request_id
        self.points = points
        self.voxel_size = voxel_size
        self.statistical = statistical
        self.stat_neighbors = stat_neighbors
        self.std_ratio = std_ratio
        self.radius = radius
        self.radius_neighbors = radius_neighbors
        self.radius_size = radius_size
        self.ranges = ranges
        self.auto = auto
        return None
    
    
    def run(self):
        try:
            points = self.points
            if self.ranges is not None:
                mask = range_mask(points, self.ranges)
            else:
                mask = None
            if mask is not None:
                scoped_count = int(np.count_nonzero(mask))
                available = available_memory_bytes()
                if not self.statistical:
                    if self.radius:
                        estimated = scoped_count * 180 + len(points) * 12
                    else:
                        estimated = scoped_count * 96 + len(points) * 12
                else:
                    estimated = scoped_count * 180 + len(points) * 12
                if available:
                    if estimated > available * 0.75:
                        raise MemoryError(
                            '当前 XYZ 范围的完整点云超过安全内存预算；请缩小范围后重算。未处理显示抽样。')
                points = points[mask]
            if not len(points):
                raise ValueError('当前 XYZ 范围没有可滤波的点。')
            if self.auto is not None:
                __temp_4914, __temp_4915, __temp_4916, __temp_4917 = self.auto
                sample_limit = __temp_4914
                voxel_bounds = __temp_4915
                radius_bounds = __temp_4916
                mode = __temp_4917
                if sample_limit:
                    stride = max(1, int(np.ceil(len(points) / sample_limit)))
                else:
                    stride = 1
                sample = points[slice(None, None, stride)]
                spacing = float(np.cbrt(np.prod(np.maximum(np.ptp(sample, axis=
                    0), 0.0001)) / len(sample)))
                __temp_4930 = [spacing * (1.25, 1.75, 2.5)[mode]]
                __temp_4930.extend(sorted(voxel_bounds))
                self.voxel_size = float(np.clip(*tuple(__temp_4930)))
                __temp_4935 = [spacing * (3, 4, 5)[mode]]
                __temp_4935.extend(sorted(radius_bounds))
                self.radius_size = float(np.clip(*tuple(__temp_4935)))
            if self.voxel_size > 0:
                cells = np.floor(points / self.voxel_size).astype(np.int32)
                __temp_4941, __temp_4942 = np.unique(cells, axis=0,
                    return_index=True)
                _ = __temp_4941
                indices = __temp_4942
                points = np.ascontiguousarray(points[np.sort(indices)])
            if self.isInterruptionRequested():
                return None
            if not self.statistical:
                if self.radius:
                    cloud = o3d.geometry.PointCloud()
                    cloud.points = o3d.utility.Vector3dVector(points)
                    if self.statistical:
                        __temp_4949, __temp_4950 = (cloud.
                            remove_statistical_outlier(nb_neighbors=self.
                            stat_neighbors, std_ratio=self.std_ratio))
                        cloud = __temp_4949
                        _ = __temp_4950
                    if self.radius:
                        if len(cloud.points):
                            __temp_4953, __temp_4954 = cloud.remove_radius_outlier(
                                nb_points=self.radius_neighbors, radius=self.
                                radius_size)
                            cloud = __temp_4953
                            _ = __temp_4954
                    points = np.asarray(cloud.points, dtype=np.float32)
            else:
                cloud = o3d.geometry.PointCloud()
                cloud.points = o3d.utility.Vector3dVector(points)
                if self.statistical:
                    __temp_4959, __temp_4960 = cloud.remove_statistical_outlier(
                        nb_neighbors=self.stat_neighbors, std_ratio=self.std_ratio)
                    cloud = __temp_4959
                    _ = __temp_4960
                if self.radius:
                    if len(cloud.points):
                        __temp_4963, __temp_4964 = cloud.remove_radius_outlier(
                            nb_points=self.radius_neighbors, radius=self.
                            radius_size)
                        cloud = __temp_4963
                        _ = __temp_4964
                points = np.asarray(cloud.points, dtype=np.float32)
            if not len(points):
                raise ValueError('滤波结果为空，已保留原始点云。')
            if mask is not None:
                points = np.concatenate((self.points[~mask], points))
            if not self.isInterruptionRequested():
                self.completed.emit(self.request_id, points)
                return None
        finally:
            return None
    
    
    __classcell__ = __class__
    return __class__
