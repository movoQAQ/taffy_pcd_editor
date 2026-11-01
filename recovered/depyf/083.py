def _toggle_region_expanded(self, expanded):
    if expanded:
        self.region_expander.setArrowType(Qt.DownArrow)
        self.region_scroll.setVisible(expanded)
    else:
        self.region_expander.setArrowType(Qt.RightArrow)
        self.region_scroll.setVisible(expanded)
    if not expanded:
        self.cancel_point_edit_mode()
        return None
    return None
