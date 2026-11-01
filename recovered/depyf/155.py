def _find_layer(self, layer_id):
    """original function name <genexpr> is illegal, use a temp name."""
    
    
    def __temp_7197(comp_arg_0):
        nonlocal layer_id
        for __temp_7198 in comp_arg_0:
            layer = __temp_7198
            if not layer['id'] == layer_id:
                continue
            yield layer
            continue
        return None
    
    
    return next(__temp_7197(iter(self.layers)), None)
