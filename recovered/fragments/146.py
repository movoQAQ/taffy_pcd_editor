# Source Generated with Decompyle++
# File: 146.pyc (Python 3.10)

layer_id = layer['id']
row = QFrame()
row.setObjectName('layerRow')
row.setStyleSheet('QFrame#layerRow { background: transparent; border: 1px solid transparent; border-radius: 4px; } QFrame#layerRow[selected="true"] { background: #e8f3ed; border-color: #c8ded3; }')
row_layout = QHBoxLayout(row)
row_layout.setContentsMargins(4, 2, 3, 2)
row_layout.setSpacing(3)
eye = QToolButton()
eye.setFixedSize(24, 26)
eye.setStyleSheet('QToolButton { border: none; background: transparent; color: #28785b; font-size: 15px; } QToolButton:hover { background: #edf4f0; border-radius: 3px; }')
eye.setToolTip('隐藏图层' if layer['visible'] else '显示图层')
eye.setText('◉' if layer['visible'] else '○')
None((lambda checked = None, target = None: self.toggle_layer_visibility(target)))
select = LayerSelectButton(layer['filename'])
select.setObjectName('layerSelect')
select.setStyleSheet('QPushButton#layerSelect { text-align: left; border: none; background: transparent; padding: 5px 2px; color: #3f504a; } QPushButton#layerSelect:hover { color: #20785b; background: transparent; }')
None((lambda checked = None, target = None: self.activate_layer(target)))
None((lambda target = None: self.show_and_activate_layer(target)))
menu_button = QToolButton()
menu_button.setText('•••')
menu_button.setFixedSize(26, 26)
menu_button.setToolTip('图层操作')
menu_button.setStyleSheet('QToolButton { border: none; background: transparent; color: #74817c; padding: 2px; } QToolButton:hover { background: #edf4f0; border-radius: 3px; }')
None((lambda checked = None, target = None, button = None: self.show_layer_menu(target, button)))
row_layout.addWidget(eye)
row_layout.addWidget(select, 1)
row_layout.addWidget(menu_button)
details = QLabel(f'''{fmt_number(layer['total_points'])} 点 · XYZ''')
details.setObjectName('muted')
wrapper = QWidget()
wrapper.setStyleSheet('background:transparent')
wrapper_layout = QVBoxLayout(wrapper)
wrapper_layout.setContentsMargins(0, 0, 0, 2)
wrapper_layout.setSpacing(0)
wrapper_layout.addWidget(row)
wrapper_layout.addWidget(details)
self.layers_layout.addWidget(wrapper)
layer['row'] = row
layer['eye'] = eye
layer['select'] = select
layer['menu_button'] = menu_button
layer['details'] = details
self.layer_rows[layer_id] = wrapper
self._refresh_layer_selection()
