def _show_region_preview(self, hull):
    self._clear_region_preview()
    points = vtk.vtkPoints()
    for __temp_6456 in iter(hull.points):
        point = __temp_6456
        points.InsertNextPoint(*map(float, point))
        continue
    faces = vtk.vtkCellArray()
    for __temp_6460 in iter(hull.simplices):
        triangle = __temp_6460
        faces.InsertNextCell(3)
        for __temp_6462 in iter(triangle):
            point_id = __temp_6462
            faces.InsertCellPoint(int(point_id))
            continue
        continue
    poly = vtk.vtkPolyData()
    poly.SetPoints(points)
    poly.SetPolys(faces)
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputData(poly)
    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    actor.GetProperty().SetColor(0.91, 0.23, 0.48)
    actor.GetProperty().SetOpacity(0.22)
    actor.GetProperty().SetEdgeVisibility(True)
    actor.GetProperty().SetEdgeColor(0.67, 0.2, 0.44)
    actor.GetProperty().SetLineWidth(1.5)
    self.renderer.AddActor(actor)
    self.region_preview_actor = actor
    self.vtk_widget.GetRenderWindow().Render()
    return None
