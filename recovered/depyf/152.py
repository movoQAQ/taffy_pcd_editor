def toggle_layer_visibility(self, layer_id):
    layer = self._find_layer(layer_id)
    if layer is None:
        return None
    layer['visible'] = not layer['visible']
    layer['actor'].SetVisibility(layer['visible'])
    if layer['visible']:
        layer['eye'].setText('◉')
    else:
        layer['eye'].setText('○')
    if layer['visible']:
        layer['eye'].setToolTip('隐藏图层')
        self.vtk_widget.GetRenderWindow().Render()
        return None
    else:
        layer['eye'].setToolTip('显示图层')
        self.vtk_widget.GetRenderWindow().Render()
        return None
