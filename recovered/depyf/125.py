def _button(self, text, name, callback, layout):
    button = QPushButton(text)
    button.setObjectName(name)
    button.clicked.connect(callback)
    layout.addWidget(button)
    return button
