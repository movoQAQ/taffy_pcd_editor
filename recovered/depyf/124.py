def _update_filter_parameter(self, key, raw_value):
    __temp_6862, __temp_6863, __temp_6864, __temp_6865 = (self.
        filter_parameter_sliders[key])
    slider = __temp_6862
    label = __temp_6863
    unit = __temp_6864
    multiplier = __temp_6865
    value = raw_value / multiplier
    label.setText(format(value, 'g') + ' ' + str(unit))
    return None
