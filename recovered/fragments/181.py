# Source Generated with Decompyle++
# File: 181.pyc (Python 3.10)

for axis, slider in (('x', self.x_range_slider), ('y', self.y_range_slider), ('z', self.z_range_slider)):
    slider.set_range(0, 1000)
    self.apply_axis_range(axis, 0, 1000)
