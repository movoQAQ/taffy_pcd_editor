# Source Generated with Decompyle++
# File: 166.pyc (Python 3.10)

for axis, slider in (('x', self.x_range_slider), ('y', self.y_range_slider), ('z', self.z_range_slider)):
    (low, high) = self.axis_bounds[axis]
    span = max(high - low, 1e-09)
    (selected_low, selected_high) = self.axis_ranges[axis]
    slider.set_range(round(((selected_low - low) / span) * 1000), round(((selected_high - low) / span) * 1000))
    suffix = ' m'
    getattr(self, f'''{axis}_overlay_low''').setText(f'''{low:.1f}{suffix}''')
    getattr(self, f'''{axis}_overlay_high''').setText(f'''{high:.1f}{suffix}''')
