def _picked_render_point_id(self, x, y):
    if not self.points is None:
        if not self.points_actor.GetVisibility():
            return -1
    else:
        return -1
    """original function name <genexpr> is illegal, use a temp name."""
    
    
    def __temp_6541(comp_arg_0):
        nonlocal self
        for __temp_6542 in comp_arg_0:
            axis = __temp_6542
            yield self.axis_ranges[axis]
            continue
        return None
    
    
    key = id(self.points), tuple(__temp_6541(iter('xyz')))
    if not self.pick_cache is None:
        if self.pick_cache[0] != key:
            visible = np.ones(len(self.points), dtype=bool)
            for __temp_6548 in iter(enumerate('xyz')):
                __temp_6549, __temp_6550 = __temp_6548
                column = __temp_6549
                axis = __temp_6550
                __temp_6551, __temp_6552 = self.axis_ranges[axis]
                low = __temp_6551
                high = __temp_6552
                visible &= (self.points[slice(None, None), column] >= low) & (self
                    .points[slice(None, None), column] <= high)
                continue
            indices = np.flatnonzero(visible)
            if not len(indices):
                return -1
            vtk_points = vtk.vtkPoints()
            vtk_points.SetData(numpy_to_vtk(np.ascontiguousarray(self.points[
                indices]), deep=True))
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
            self.pick_cache = key, indices, actor
    else:
        visible = np.ones(len(self.points), dtype=bool)
        for __temp_6574 in iter(enumerate('xyz')):
            __temp_6575, __temp_6576 = __temp_6574
            column = __temp_6575
            axis = __temp_6576
            __temp_6577, __temp_6578 = self.axis_ranges[axis]
            low = __temp_6577
            high = __temp_6578
            visible &= (self.points[slice(None, None), column] >= low) & (self.
                points[slice(None, None), column] <= high)
            continue
        indices = np.flatnonzero(visible)
        if not len(indices):
            return -1
        vtk_points = vtk.vtkPoints()
        vtk_points.SetData(numpy_to_vtk(np.ascontiguousarray(self.points[
            indices]), deep=True))
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
        self.pick_cache = key, indices, actor
    __temp_6597, __temp_6598, __temp_6599 = self.pick_cache
    _ = __temp_6597
    indices = __temp_6598
    actor = __temp_6599
    picker = vtk.vtkPointPicker()
    __temp_6603, __temp_6604 = self.vtk_widget.GetRenderWindow().GetSize()
    render_width = __temp_6603
    render_height = __temp_6604
    picker.SetTolerance(18 / max(1, np.hypot(render_width, render_height)))
    picker.PickFromListOn()
    picker.AddPickList(actor)
    self.renderer.AddActor(actor)
    try:
        if not picker.Pick(x, y, 0, self.renderer):
            self.renderer.RemoveActor(actor)
            return -1
    finally:
        self.renderer.RemoveActor(actor)
    picked_actor = picker.GetActor()
    if not picked_actor is None:
        if picked_actor.GetAddressAsString('') != actor.GetAddressAsString(''):
            return -1
    else:
        return -1
    point_id = picker.GetPointId()
    if 0 <= point_id:
        if point_id < len(indices):
            return int(indices[point_id])
    return -1
