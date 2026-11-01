# Source Generated with Decompyle++
# File: 160.pyc (Python 3.10)

points = np.asarray(points, np.float32, **('dtype',))
points = points[np.isfinite(points).all(1, **('axis',))]
if not len(points):
    raise ValueError('文件中没有有效的 XYZ 点。')
source_z = full_z if full_z is not None else points[(:, 2)]
z_min = float(np.nanmin(source_z))
z_max = float(np.nanmax(source_z))
if z_max - z_min < 1e-06:
    z_max = z_min + 0.001
complete = None if full_points is None else np.asarray(full_points, np.float32, **('dtype',))
if complete is not None:
    complete = complete[np.isfinite(complete).all(1, **('axis',))]
    if not len(complete):
        complete = None
bounds_source = complete if complete is not None else points
bounds_min = np.nanmin(bounds_source, 0, **('axis',))
bounds_max = np.nanmax(bounds_source, 0, **('axis',))
if complete is not None:
    z_min = float(complete[(:, 2)].min())
    z_max = float(complete[(:, 2)].max())
    if z_max - z_min < 1e-06:
        z_max = z_min + 0.001
bounds_min[2] = z_min
bounds_max[2] = z_max
axis_bounds = (lambda .0 = None: pass# WARNING: Decompyle incomplete
)(enumerate(('x', 'y', 'z')))
if not self.layers:
    actor = self.points_actor
    mapper = self.mapper
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
if not total_points:
    pass
layer = {
    'id': self.next_layer_id,
    'title': title,
    'filename': filename,
    'source_path': source_path,
    'source_points': points,
    'display_points': points.copy(),
    'full_z': source_z,
    'total_points': int(len(source_z)),
    'axis_bounds': axis_bounds,
    'axis_ranges': dict(axis_bounds),
    'visible': True,
    'actor': actor,
    'mapper': mapper,
    'row': None }
if complete is not None:
    layer['edit_points'] = np.ascontiguousarray(complete, np.float32, **('dtype',))
    layer['full_z'] = layer['edit_points'][(:, 2)]
    layer['total_points'] = len(layer['edit_points'])
self.next_layer_id += 1
self.layers.append(layer)
self._add_layer_row(layer)
self.activate_layer(layer['id'], True, **('reset_camera',))
