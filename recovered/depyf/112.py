def _finish_completion(self, layer_id, base, result, spacing):
    __temp_6732, __temp_6733 = result
    points = __temp_6732
    count = __temp_6733
    if layer_id != self.active_layer_id:
        return None
    if self.completion_base_points is None:
        self.completion_base_points = base
    self._replace_active_source_points(points)
    self.region_pick_status.setText('已补全 ' + str(fmt_number(count)) +
        ' 个点，间距约 ' + format(spacing, '.2f') + ' m。')
    return None
