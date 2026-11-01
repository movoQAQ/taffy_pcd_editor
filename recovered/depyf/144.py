def <genexpr>(comp_arg_0):
    nonlocal ca, cb, f
    for __temp_7074 in comp_arg_0:
        j = __temp_7074
        yield ca[j] * (1 - f) + cb[j] * f
        continue
    return None
