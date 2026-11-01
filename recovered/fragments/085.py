# Source Generated with Decompyle++
# File: 085.pyc (Python 3.10)

if self.point_edit_mode == 'delete':
    self.point_edit_mode = None
    self._set_point_pick_mode(False)
    self.region_pick_status.setText(f'''已选 {len(self.region_pick_points)} 个点；点击“计算凸包区域”。''')
    return None
