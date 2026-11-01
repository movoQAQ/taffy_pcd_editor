def <dictcomp>(comp_arg_0):
    nonlocal bounds_max, bounds_min
    __temp_7274 = {}
    for __temp_7275 in comp_arg_0:
        __temp_7276, __temp_7277 = __temp_7275
        i = __temp_7276
        axis = __temp_7277
        __temp_7274.__setitem__(axis, (float(bounds_min[i]), float(bounds_max[i])))
        continue
    return __temp_7274
