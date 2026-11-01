def activate_layer(self, layer_id, reset_camera):
    layer = self._find_layer(layer_id)
    if layer is None:
        return None
    if layer_id != self.active_layer_id:
        if self._editing_busy():
            self.filter_status.setText('后台任务运行中，完成后可切换编辑图层。')
            return None
    if self.active_layer_id is not None:
        previous = self._find_layer(self.active_layer_id)
    else:
        previous = None
    if previous is not layer:
        self.point_edit_mode = None
        self.region_pick_points.clear()
        self.region_pick_scope = None
        self.selected_hull_equations = None
        self.selected_region_vertices = None
        self._clear_region_markers()
        self.completion_base_points = None
        self.completion_markers.clear()
        self._set_point_pick_mode(False)
    if previous is not None:
        previous['display_points'] = self.points.copy()
        previous['axis_ranges'] = dict(self.axis_ranges)
        previous['mapper'].RemoveAllClippingPlanes()
        self.filter_request_id += 1
        self.filter_request_id = self.filter_request_id
    else:
        self.filter_request_id += 1
        self.filter_request_id = self.filter_request_id
    self.active_layer_id = layer_id
    self.points_actor = layer['actor']
    self.mapper = layer['mapper']
    self.render_source_points = layer['source_points']
    self.full_z = layer['full_z']
    self.total_points = layer['total_points']
    __temp_7291, __temp_7292 = layer['axis_bounds']['z']
    self.z_min = __temp_7291
    self.z_max = __temp_7292
    if self.z_max - self.z_min < 1e-06:
        self.z_max = self.z_min + 0.001
    self.axis_bounds = dict(layer['axis_bounds'])
    self.axis_ranges = dict(layer['axis_ranges'])
    self.mapper.SetLookupTable(self.lookup)
    self.mapper.SetScalarRange(self.z_min, self.z_max)
    self.mapper.RemoveAllClippingPlanes()
    self.lookup.SetTableRange(self.z_min, self.z_max)
    for __temp_7299 in iter((('x', self.x_low_plane, self.x_high_plane, (1, 0, 
        0), (-1, 0, 0)), ('y', self.y_low_plane, self.y_high_plane, (0, 1, 0),
        (0, -1, 0)), ('z', self.low_plane, self.high_plane, (0, 0, 1), (0, 0, -1)))
        ):
        __temp_7300, __temp_7301, __temp_7302, __temp_7303, __temp_7304 = (
            __temp_7299)
        axis = __temp_7300
        low_plane = __temp_7301
        high_plane = __temp_7302
        low_normal = __temp_7303
        high_normal = __temp_7304
        low_plane.SetNormal(*low_normal)
        high_plane.SetNormal(*high_normal)
        """original function name <listcomp> is illegal, use a temp name."""
    
        def __temp_7307(comp_arg_0):
            nonlocal axis, self
            __temp_7308 = []
            for __temp_7309 in comp_arg_0:
                j = __temp_7309
                if j == 'xyz'.index(axis):
                    __temp_7308.append(self.axis_ranges[axis][0])
                else:
                    __temp_7308.append(0)
                continue
            return __temp_7308
        low_plane.SetOrigin(*__temp_7307(iter(range(3))))
        """original function name <listcomp> is illegal, use a temp name."""
    
        def __temp_7314(comp_arg_0):
            nonlocal axis, self
            __temp_7315 = []
            for __temp_7316 in comp_arg_0:
                j = __temp_7316
                if j == 'xyz'.index(axis):
                    __temp_7315.append(self.axis_ranges[axis][1])
                else:
                    __temp_7315.append(0)
                continue
            return __temp_7315
        high_plane.SetOrigin(*__temp_7314(iter(range(3))))
        self.mapper.AddClippingPlane(low_plane)
        self.mapper.AddClippingPlane(high_plane)
        continue
    self.points_actor.SetVisibility(layer['visible'])
    self._set_render_points(layer['display_points'])
    self.header_file.setText(layer['title'])
    self.layer_name.setText(layer['filename'])
    points = self.render_source_points
    self.layer_points.setText(str(fmt_number(self.total_points)) + ' 点   ·   XYZ')
    if self.total_points > len(points):
        self.layer_points.setText(str(fmt_number(self.total_points)) +
            ' 点   ·   视图抽样 ' + str(fmt_number(len(points))))
        self.metric_points.setText(fmt_number(self.total_points))
        self.metric_height.setText(format(self.z_min, '.1f') + ' — ' + format(
            self.z_max, '.1f') + ' m')
        self._refresh_layer_selection()
        self._set_slider_extent()
        self._update_visible_stats()
        self.render_count.setText('渲染 ' + str(fmt_number(len(self.points))) +
            ' 点 · 原始 ' + str(fmt_number(self.total_points)) + ' 点')
        self.filter_status.setText('选中图层可编辑；滤波需点击“重新计算滤波”应用。')
    else:
        self.metric_points.setText(fmt_number(self.total_points))
        self.metric_height.setText(format(self.z_min, '.1f') + ' — ' + format(
            self.z_max, '.1f') + ' m')
        self._refresh_layer_selection()
        self._set_slider_extent()
        self._update_visible_stats()
        self.render_count.setText('渲染 ' + str(fmt_number(len(self.points))) +
            ' 点 · 原始 ' + str(fmt_number(self.total_points)) + ' 点')
        self.filter_status.setText('选中图层可编辑；滤波需点击“重新计算滤波”应用。')
    if not reset_camera:
        if previous is not layer:
            self.reset_camera()
            return None
    else:
        self.reset_camera()
        return None
    self.vtk_widget.GetRenderWindow().Render()
    return None
