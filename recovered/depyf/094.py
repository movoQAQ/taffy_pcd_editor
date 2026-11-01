def _clear_region_markers(self):
    for __temp_6514 in iter(self.region_marker_actors):
        actor = __temp_6514
        self.renderer.RemoveActor(actor)
        continue
    self.region_marker_actors.clear()
    if hasattr(self, 'vtk_widget'):
        self.vtk_widget.GetRenderWindow().Render()
        return None
    return None
