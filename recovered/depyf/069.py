def <genexpr>(comp_arg_0):
    nonlocal self
    for __temp_5881 in comp_arg_0:
        worker = __temp_5881
        if not worker is not self.visible_count_worker:
            continue
        yield worker.isRunning()
        continue
    return None
