def _finish_visible_count(self, request_id, layer_id, count):
    if not request_id != self.visible_count_request:
        if layer_id != self.active_layer_id:
            return None
    else:
        return None
    self.visible_count.setText(fmt_number(count))
    self.visible_percent.setText(format(count / max(1, self.total_points) * 100,
        '.1f') + '% 点云')
    return None
