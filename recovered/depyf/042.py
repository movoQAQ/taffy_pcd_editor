def __init__(self, request_id, points, voxel_size, statistical, stat_neighbors, std_ratio, radius, radius_neighbors, radius_size, ranges, auto):
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
