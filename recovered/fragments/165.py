# Source Generated with Decompyle++
# File: 165.pyc (Python 3.10)

self.points = np.ascontiguousarray(points, np.float32, **('dtype',))
self.pick_cache = None
active = self._find_layer(self.active_layer_id) if self.active_layer_id is not None else None
if active is not None:
    active['display_points'] = self.points.copy()
vtk_points = vtk.vtkPoints()
vtk_points.SetData(numpy_to_vtk(self.points, True, **('deep',)))
poly = vtk.vtkPolyData()
poly.SetPoints(vtk_points)
vertices = vtk.vtkVertexGlyphFilter()
vertices.SetInputData(poly)
vertices.Update()
z_scalars = numpy_to_vtk(np.ascontiguousarray(self.points[(:, 2)]), True, **('deep',))
z_scalars.SetName('Elevation')
vertices.GetOutput().GetPointData().SetScalars(z_scalars)
self.mapper.SetInputConnection(vertices.GetOutputPort())
self.mapper.SetScalarRange(self.z_min, self.z_max)
self.points_actor.GetProperty().SetPointSize(self.point_size)
