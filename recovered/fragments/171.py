# Source Generated with Decompyle++
# File: 171.pyc (Python 3.10)

if request_id != self.visible_count_request or layer_id != self.active_layer_id:
    return None
None.visible_count.setText(fmt_number(count))
self.visible_percent.setText(f'''{(count / max(1, self.total_points)) * 100:.1f}% 点云''')
