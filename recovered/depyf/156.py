def <genexpr>(comp_arg_0):
    nonlocal layer_id
    for __temp_7201 in comp_arg_0:
        layer = __temp_7201
        if not layer['id'] == layer_id:
            continue
        yield layer
        continue
    return None
