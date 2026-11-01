def show_and_activate_layer(self, layer_id):
    layer = self._find_layer(layer_id)
    if layer is not None:
        if not layer['visible']:
            self.toggle_layer_visibility(layer_id)
            self.activate_layer(layer_id)
            return None
        else:
            self.activate_layer(layer_id)
            return None
    else:
        self.activate_layer(layer_id)
        return None
