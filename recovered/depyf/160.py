def set_cloud(self, points, title, filename, full_z, total_points, source_path, full_points):
    points = np.asarray(points, dtype=np.float32)
    points = points[np.isfinite(points).all(axis=1)]
    if not len(points):
        raise ValueError('文件中没有有效的 XYZ 点。')
    if full_z is not None:
        source_z = full_z
    else:
        source_z = points[slice(None, None), 2]
    z_min = float(np.nanmin(source_z))
    z_max = float(np.nanmax(source_z))
    if z_max - z_min < 1e-06:
        z_max = z_min + 0.001
    if full_points is None:
        complete = None
    else:
        complete = np.asarray(full_points, dtype=np.float32)
    if complete is not None:
        complete = complete[np.isfinite(complete).all(axis=1)]
        if not len(complete):
            complete = None
    if complete is not None:
        bounds_source = complete
    else:
        bounds_source = points
    bounds_min = np.nanmin(bounds_source, axis=0)
    bounds_max = np.nanmax(bounds_source, axis=0)
    if complete is not None:
        z_min = float(complete[slice(None, None), 2].min())
        z_max = float(complete[slice(None, None), 2].max())
        if z_max - z_min < 1e-06:
            z_max = z_min + 0.001
    bounds_min[2] = z_min
    bounds_max[2] = z_max
    """original function name <dictcomp> is illegal, use a temp name."""
    
    
    def __temp_7241(comp_arg_0):
        nonlocal bounds_max, bounds_min
        __temp_7242 = {}
        for __temp_7243 in comp_arg_0:
            __temp_7244, __temp_7245 = __temp_7243
            i = __temp_7244
            axis = __temp_7245
            __temp_7242.__setitem__(axis, (float(bounds_min[i]), float(
                bounds_max[i])))
            continue
        return __temp_7242
    
    
    axis_bounds = __temp_7241(iter(enumerate(('x', 'y', 'z'))))
    if not self.layers:
        actor = self.points_actor
        mapper = self.mapper
        __temp_7250 = points.copy()
    else:
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetLookupTable(self.lookup)
        mapper.SetScalarModeToUsePointFieldData()
        mapper.SelectColorArray('Elevation')
        mapper.SetScalarVisibility(True)
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetPointSize(self.point_size)
        self.renderer.AddActor(actor)
        points.copy()
    if not total_points:
        layer = {id: self.next_layer_id, title: title, filename: filename,
            source_path: source_path, source_points: points, display_points:
            __temp_7250, full_z: source_z, total_points: int(len(source_z)),
            axis_bounds: axis_bounds, axis_ranges: dict(axis_bounds), visible: 
            True, actor: actor, mapper: mapper, row: None}
    else:
        layer = {id: self.next_layer_id, title: title, filename: filename,
            source_path: source_path, source_points: points, display_points:
            __temp_7250, full_z: source_z, total_points: int(total_points),
            axis_bounds: axis_bounds, axis_ranges: dict(axis_bounds), visible: 
            True, actor: actor, mapper: mapper, row: None}
    if complete is not None:
        layer['edit_points'] = np.ascontiguousarray(complete, dtype=np.float32)
        layer['full_z'] = layer['edit_points'][slice(None, None), 2]
        layer['total_points'] = len(layer['edit_points'])
    self.next_layer_id += 1
    self.next_layer_id = self.next_layer_id
    self.layers.append(layer)
    self._add_layer_row(layer)
    self.activate_layer(layer['id'], reset_camera=True)
    return None
