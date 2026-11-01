def <listcomp>(comp_arg_0):
    nonlocal bounds
    __temp_7548 = []
    for __temp_7549 in comp_arg_0:
        i = __temp_7549
        __temp_7548.append((bounds[i] + bounds[i + 1]) * 0.5)
        continue
    return __temp_7548
