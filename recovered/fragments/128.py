# Source Generated with Decompyle++
# File: 128.pyc (Python 3.10)

if not self.auto_density.isChecked() or len(points):
    size = self.voxel_slider.value() / 100
    self.voxel_value.setText(f'''{size:.2f} m''')
    return size
max_samples = None.filter_parameter_sliders['auto_sample'][0].value() * 10000
stride = max(1, int(np.ceil(len(points) / max_samples)))
sample = points[::stride]
spans = np.ptp(sample, 0, **('axis',))
spacing = float(np.cbrt(np.prod(np.maximum(spans, 0.0001)) / len(sample)))
auto_min = self.filter_parameter_sliders['auto_min_voxel'][0].value() / 100
auto_max = self.filter_parameter_sliders['auto_max_voxel'][0].value() / 100
mode_scale = (1.25, 1.75, 2.5)[self.auto_mode.currentIndex()]
size = float(np.clip(spacing * mode_scale, min(auto_min, auto_max), max(auto_min, auto_max)))
self.voxel_value.setText(f'''自动 {size:.2f} m''')
return size
