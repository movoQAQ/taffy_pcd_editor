def <genexpr>(comp_arg_0):
    nonlocal point, scope
    for __temp_6630 in comp_arg_0:
        __temp_6631, __temp_6632 = __temp_6630
        i = __temp_6631
        axis = __temp_6632
        if scope[axis][0] <= point[i]:
            yield point[i] <= scope[axis][1]
        else:
            yield scope[axis][0] <= point[i]
        continue
    return None
