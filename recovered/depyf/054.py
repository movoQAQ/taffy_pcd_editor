def __init__(self, request_id, path, include_bounds):
    nonlocal __class__
    super().__init__()
    self.request_id = request_id
    self.path = path
    self.include_bounds = include_bounds
    return None
