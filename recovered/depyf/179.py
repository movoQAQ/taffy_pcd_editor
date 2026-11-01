def <dictcomp>(comp_arg_0):
    nonlocal bounds_max, bounds_min
    __temp_7512 = {}
    for __temp_7513 in comp_arg_0:
        __temp_7514, __temp_7515 = __temp_7513
        i = __temp_7514
        axis = __temp_7515
        __temp_7512.__setitem__(axis, (float(bounds_min[i]), float(bounds_max[i])))
        continue
    return __temp_7512
