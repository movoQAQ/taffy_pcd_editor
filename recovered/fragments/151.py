# Source Generated with Decompyle++
# File: 151.pyc (Python 3.10)

for layer in self.layers:
    row = layer.get('row')
    if row is None:
        continue
    row.setProperty('selected', layer['id'] == self.active_layer_id)
    row.style().unpolish(row)
    row.style().polish(row)
    row.update()
