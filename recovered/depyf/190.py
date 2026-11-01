def toggle_grid(self):
    self.grid_visible = not self.grid_visible
    self.grid_actor.SetVisibility(self.grid_visible)
    self.vtk_widget.GetRenderWindow().Render()
    return None
