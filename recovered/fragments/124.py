# Source Generated with Decompyle++
# File: 124.pyc (Python 3.10)

(slider, label, unit, multiplier) = self.filter_parameter_sliders[key]
value = raw_value / multiplier
label.setText(f'''{value:g} {unit}''')
