def rotate_around_z(self, degrees):
    camera = self.renderer.GetActiveCamera()
    focal = np.asarray(camera.GetFocalPoint(), dtype=float)
    position = np.asarray(camera.GetPosition(), dtype=float)
    view_up = np.asarray(camera.GetViewUp(), dtype=float)
    angle = np.deg2rad(degrees)
    rotation = np.array(((np.cos(angle), -np.sin(angle)), (np.sin(angle), np.
        cos(angle))))
    offset = position - focal
    offset[slice(None, 2)] = rotation @ offset[slice(None, 2)]
    view_up[slice(None, 2)] = rotation @ view_up[slice(None, 2)]
    camera.SetPosition(*(focal + offset))
    camera.SetViewUp(*view_up)
    camera.OrthogonalizeViewUp()
    self.renderer.ResetCameraClippingRange()
    self.vtk_widget.GetRenderWindow().Render()
    return None
