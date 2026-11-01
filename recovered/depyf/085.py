def finish_region_selection(self):
    if self.point_edit_mode == 'delete':
        self.point_edit_mode = None
        self._set_point_pick_mode(False)
        self.region_pick_status.setText('已选 ' + str(len(self.region_pick_points
            )) + ' 个点；点击“计算凸包区域”。')
        return None
    return None
