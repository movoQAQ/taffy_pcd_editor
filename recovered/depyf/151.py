def _refresh_layer_selection(self):
    for __temp_7159 in iter(self.layers):
        layer = __temp_7159
        row = layer.get('row')
        if row is None:
            continue
            row.setProperty('selected', layer['id'] == self.active_layer_id)
            row.style().unpolish(row)
            row.style().polish(row)
            row.update()
        else:
            row.setProperty('selected', layer['id'] == self.active_layer_id)
            row.style().unpolish(row)
            row.style().polish(row)
            row.update()
        continue
    return None
