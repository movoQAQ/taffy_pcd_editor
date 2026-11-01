def <lambda>():
    nonlocal self, worker
    if self.full_load_worker is worker:
        return setattr(self, 'full_load_worker', None)
    return None
