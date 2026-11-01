def _add_filter_parameter(self, layout, title, key, minimum, maximum, default, unit, multiplier):
    row = QHBoxLayout()
    label = QLabel(title)
    label.setObjectName('muted')
    value = QLabel()
    value.setStyleSheet('color:#40584e;background:transparent')
    row.addWidget(label)
    row.addStretch()
    row.addWidget(value)
    layout.addLayout(row)
    slider = DragOnlySlider(Qt.Horizontal)
    slider.setRange(minimum, maximum)
    slider.setValue(default)
    """original function name <lambda> is illegal, use a temp name."""
    
    
    def __temp_6855(value, parameter):
        nonlocal self
        return self._update_filter_parameter(parameter, value)
    
    
    slider.valueChanged.connect(__temp_6855)
    slider.valueChanged.connect(self.schedule_display_filter)
    layout.addWidget(slider)
    self.filter_parameter_sliders[key] = slider, value, unit, multiplier
    self._update_filter_parameter(key, default)
    return None
