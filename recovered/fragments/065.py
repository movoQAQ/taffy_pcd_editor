# Source Generated with Decompyle++
# File: 065.pyc (Python 3.10)

super().__init__()
self.setWindowTitle('taffy编辑器')
self.setWindowIcon(QIcon(str(Path(__file__).parent / 'assets' / 'tafei-pcd-editor.png')))
self.resize(1440, 920)
self.setMinimumSize(1180, 700)
self.points = None
self.render_source_points = None
self.full_z = None
self.total_points = 0
self.layers = []
self.layer_rows = { }
self.active_layer_id = None
self.next_layer_id = 1
self._window_drag_offset = None
(self.z_min, self.z_max) = (-1.2, 8.4)
self.grid_visible = True
self.orthographic = False
self.point_size = 3.0
self.rotate_direction = 0
self.rotate_clock = QElapsedTimer()
self.rotate_timer = QTimer(self)
self.rotate_timer.setInterval(16)
self.rotate_timer.timeout.connect(self._rotate_held_view)
self.filter_request_id = 0
self.filter_recalculate_requested = False
self.filter_worker = None
self.filter_scope = None
self.filter_result_popup = None
self.point_edit_mode = None
self.region_pick_points = []
self.region_pick_scope = None
self.pick_cache = None
self.region_marker_actors = []
self.selected_hull_equations = None
self.selected_region_vertices = None
self.region_preview_actor = None
self.edit_load_operation = None
self.completion_base_points = None
self.completion_markers = []
self.last_completion_click = None
self.last_edit_click_time = 0.0
self.last_edit_click_pos = None
self.edit_load_worker = None
self.edit_load_request = 0
self.full_load_worker = None
self.full_load_request = 0
self.full_load_workers = { }
self.visible_count_worker = None
self.visible_count_request = 0
self.task_workers = set()
self.edit_task_worker = None
self.region_delete_worker = None
self.region_delete_request = 0
self.filter_debounce = QTimer(self)
self.filter_debounce.setSingleShot(True)
self.filter_debounce.setInterval(260)
self.filter_debounce.timeout.connect(self.start_display_filter)
self.visible_stats_timer = QTimer(self)
self.visible_stats_timer.setSingleShot(True)
self.visible_stats_timer.setInterval(140)
self.visible_stats_timer.timeout.connect(self._update_visible_stats)
self._build_ui()
self._build_vtk()
self.header_file.setText('未导入点云')
self.layer_name.setText('等待导入')
self.layer_points.setText('0 点')
self.metric_points.setText('0')
self.metric_height.setText('--')
self.visible_count.setText('0')
self.visible_percent.setText('0% 点云')
