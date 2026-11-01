def _hold_rotate_button(self, symbol, tooltip, direction, layout):
    button = QPushButton(symbol)
    button.setObjectName('flat')
    button.setFixedWidth(30)
    button.setToolTip(tooltip)
    """original function name <lambda> is illegal, use a temp name."""
    
    
    def __temp_6875():
        nonlocal direction, self
        return self.start_held_rotation(direction)
    
    
    button.pressed.connect(__temp_6875)
    button.released.connect(self.stop_held_rotation)
    layout.addWidget(button)
    return button
