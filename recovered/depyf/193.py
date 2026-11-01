def set_point_size(self, size):
    self.point_size = float(size)
    self.points_actor.GetProperty().SetPointSize(self.point_size)
    self.size_text.setText(str(size) + ' px')
    self.vtk_widget.GetRenderWindow().Render()
    return None
