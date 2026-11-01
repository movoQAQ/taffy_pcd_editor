def <listcomp>(comp_arg_0):
    nonlocal axis, self
    __temp_7363 = []
    for __temp_7364 in comp_arg_0:
        j = __temp_7364
        if j == 'xyz'.index(axis):
            __temp_7363.append(self.axis_ranges[axis][1])
        else:
            __temp_7363.append(0)
        continue
    return __temp_7363
