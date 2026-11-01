def <lambda>(job, error, target):
    nonlocal self
    return self._fail_full_load(job, target, error)
