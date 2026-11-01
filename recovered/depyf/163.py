def <listcomp>(comp_arg_0):
    nonlocal axis, self
    __temp_7360 = []
    for __temp_7361 in comp_arg_0:
        j = __temp_7361
        if j == 'xyz'.index(axis):
            __temp_7360.append(self.axis_ranges[axis][0])
        else:
            __temp_7360.append(0)
        continue
    return __temp_7360
