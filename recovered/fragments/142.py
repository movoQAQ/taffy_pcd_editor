# Source Generated with Decompyle++
# File: 142.pyc (Python 3.10)

if self.filter_enabled.isChecked():
    self.filter_enabled.setChecked(False)
else:
    self._set_render_points(self.render_source_points)
    self.vtk_widget.GetRenderWindow().Render()
self.filter_status.setText('已恢复原始视图副本。')
