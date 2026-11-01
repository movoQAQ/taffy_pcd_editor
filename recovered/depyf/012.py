def <genexpr>(comp_arg_0):
    nonlocal counts, sizes, types
    for __temp_4538 in comp_arg_0:
        i = __temp_4538
        if sizes[i] == 4:
            if types[i] == 'F':
                yield counts[i] == 1
            else:
                yield types[i] == 'F'
        else:
            yield sizes[i] == 4
        continue
    return None
