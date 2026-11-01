# Source Generated with Decompyle++
# File: 103.pyc (Python 3.10)

if self.point_edit_mode != 'completion':
    return None
point = None._picked_visible_point(x, y)
if point is None:
    self.region_pick_status.setText('没有命中点云，请双击点云点位。')
    return None
None.complete_cloud_at(point)
