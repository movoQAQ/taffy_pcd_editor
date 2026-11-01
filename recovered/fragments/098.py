# Source Generated with Decompyle++
# File: 098.pyc (Python 3.10)

if not self.points is None or self.points_actor.GetVisibility():
    return -1
key = (None, None((lambda .0 = None: for axis in .0:
self.axis_ranges[axis])('xyz')))
if self.pick_cache is None or self.pick_cache[0] != key:
    visible = np.ones(len(self.points), bool, **('dtype',))
    for column, axis in enumerate('xyz'):
        (low, high) = self.axis_ranges[axis]
        visible &= (self.points[(:, column)] >= low) & (self.points[(:, column)] <= high)
    indices = np.flatnonzero(visible)
    if not len(indices):
        return -1
    vtk_points = None.vtkPoints()
    vtk_points.SetData(numpy_to_vtk(np.ascontiguousarray(self.points[indices]), True, **('deep',)))
    poly = vtk.vtkPolyData()
    poly.SetPoints(vtk_points)
    glyphs = vtk.vtkVertexGlyphFilter()
    glyphs.SetInputData(poly)
    glyphs.Update()
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputData(glyphs.GetOutput())
    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    actor.GetProperty().SetOpacity(0.001)
    self.pick_cache = (key, indices, actor)
(_, indices, actor) = self.pick_cache
picker = vtk.vtkPointPicker()
(render_width, render_height) = self.vtk_widget.GetRenderWindow().GetSize()
picker.SetTolerance(18 / max(1, np.hypot(render_width, render_height)))
picker.PickFromListOn()
picker.AddPickList(actor)
self.renderer.AddActor(actor)

try:
    if not picker.Pick(x, y, 0, self.renderer):
        pass
finally:
    self.renderer.RemoveActor(actor)
    return -1
    self.renderer.RemoveActor(actor)
picked_actor = picker.GetActor()
if picked_actor is None or picked_actor.GetAddressAsString('') != actor.GetAddressAsString(''):
    return -1
point_id = None.GetPointId()
if point_id <= point_id or point_id < len(indices):
    pass
else:
    0

return int(indices[point_id])
return -1
