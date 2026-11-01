# Source Generated with Decompyle++
# File: 152.pyc (Python 3.10)

layer = self._find_layer(layer_id)
if layer is None:
    return None
layer['visible'] = not None['visible']
layer['actor'].SetVisibility(layer['visible'])
layer['eye'].setText('◉' if layer['visible'] else '○')
layer['eye'].setToolTip('隐藏图层' if layer['visible'] else '显示图层')
self.vtk_widget.GetRenderWindow().Render()
