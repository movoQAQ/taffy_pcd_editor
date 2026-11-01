# Source Generated with Decompyle++
# File: 132.pyc (Python 3.10)

self.filter_request_id += 1
if enabled:
    self.schedule_display_filter()
    return None
self.filter_debounce.stop()
self._set_render_points(self.render_source_points)
self.filter_status.setText('滤波已关闭，显示原始视图副本。')
self.render_count.setText(f'''渲染 {fmt_number(len(self.points))} 点''')
self.vtk_widget.GetRenderWindow().Render()
