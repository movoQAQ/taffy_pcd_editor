def _set_render_points(self, points):
    self.points = np.ascontiguousarray(points, dtype=np.float32)
    self.pick_cache = None
    if self.active_layer_id is not None:
        active = self._find_layer(self.active_layer_id)
    else:
        active = None
    if active is not None:
        active['display_points'] = self.points.copy()
    vtk_points = vtk.vtkPoints()
    vtk_points.SetData(numpy_to_vtk(self.points, deep=True))
    poly = vtk.vtkPolyData()
    poly.SetPoints(vtk_points)
    vertices = vtk.vtkVertexGlyphFilter()
    vertices.SetInputData(poly)
    vertices.Update()
    z_scalars = numpy_to_vtk(np.ascontiguousarray(self.points[slice(None, None),
        2]), deep=True)
    z_scalars.SetName('Elevation')
    vertices.GetOutput().GetPointData().SetScalars(z_scalars)
    self.mapper.SetInputConnection(vertices.GetOutputPort())
    self.mapper.SetScalarRange(self.z_min, self.z_max)
    self.points_actor.GetProperty().SetPointSize(self.point_size)
    return None
