def <lambda>(job):
    nonlocal self
    return self.full_load_workers.pop(job, None)
