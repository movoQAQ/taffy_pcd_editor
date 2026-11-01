# Source Generated with Decompyle++
# File: 086.pyc (Python 3.10)

selected = np.asarray(self.region_pick_points, np.float64, **('dtype',))
if len(np.unique(selected, 0, **('axis',))) < 4:
    self.region_pick_status.setText('至少双击选择 4 个不同的点。')
    return None
expand_m = None.filter_parameter_sliders['region_expand'][0].value() / 100
# WARNING: Decompyle incomplete
