def _delete_region_from_points(self, points):
    equations = self.selected_hull_equations
    vertices = self.selected_region_vertices
    if not equations is None:
        if vertices is None:
            return None
    else:
        return None
    self.region_delete_request += 1
    self.region_delete_request = self.region_delete_request
    request_id = self.region_delete_request
    self.region_delete_layer_id = self.active_layer_id
    self.region_delete_equations = equations.copy()
    self.region_delete_bounds = vertices.min(axis=0), vertices.max(axis=0)
    self.region_delete_expand_m = self.filter_parameter_sliders['region_expand'][0
        ].value() / 100
    """original function name <listcomp> is illegal, use a temp name."""
    
    
    def __temp_6750(comp_arg_0):
        nonlocal self
        __temp_6751 = []
        for __temp_6752 in comp_arg_0:
            axis = __temp_6752
            __temp_6751.append(self.axis_ranges[axis])
            continue
        return __temp_6751
    
    
    visible_ranges = np.array(__temp_6750(iter('xyz')), dtype=np.float64)
    worker = RegionDeleteWorker(request_id, points, equations, self.
        region_delete_bounds, visible_ranges)
    worker.completed.connect(self._finish_region_delete)
    worker.failed.connect(self._fail_region_delete)
    self._track_worker(worker)
    self.region_delete_worker = worker
    self.delete_region_button.setEnabled(False)
    self.region_pick_status.setText('正在后台删除 ' + str(fmt_number(len(points))) +
        ' 点中的选定区域…')
    worker.start()
    return None
