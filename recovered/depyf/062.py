def __init__(self, request_id, layer_id, points, ranges):
    nonlocal __class__
    super().__init__()
    self.request_id = request_id
    self.layer_id = layer_id
    self.points = points
    self.ranges = ranges
    return None
