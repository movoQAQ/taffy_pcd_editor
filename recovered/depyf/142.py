def restore_display_points(self):
    if self.filter_enabled.isChecked():
        self.filter_enabled.setChecked(False)
        self.filter_status.setText('已恢复原始视图副本。')
        return None
    else:
        self._set_render_points(self.render_source_points)
        self.vtk_widget.GetRenderWindow().Render()
        self.filter_status.setText('已恢复原始视图副本。')
        return None
