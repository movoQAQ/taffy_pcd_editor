def _make_grid(self):
    points = vtk.vtkPoints()
    lines = vtk.vtkCellArray()
    __temp_7077, __temp_7078 = 50, 5
    extent = __temp_7077
    step = __temp_7078
    for __temp_7080 in iter(range(-extent, extent + 1, step)):
        pos = __temp_7080
        for __temp_7081 in iter((((-extent, pos, -0.45), (extent, pos, -0.45)),
            ((pos, -extent, -0.45), (pos, extent, -0.45)))):
            __temp_7082, __temp_7083 = __temp_7081
            a = __temp_7082
            b = __temp_7083
            idx = points.GetNumberOfPoints()
            points.InsertNextPoint(*a)
            points.InsertNextPoint(*b)
            lines.InsertNextCell(2)
            lines.InsertCellPoint(idx)
            lines.InsertCellPoint(idx + 1)
            continue
        continue
    poly = vtk.vtkPolyData()
    poly.SetPoints(points)
    poly.SetLines(lines)
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputData(poly)
    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    actor.GetProperty().SetColor(0.78, 0.69, 0.8)
    actor.GetProperty().SetOpacity(0.58)
    actor.GetProperty().SetLineWidth(1)
    return actor
