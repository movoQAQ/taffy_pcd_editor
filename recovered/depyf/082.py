def _toggle_filter_expanded(self, expanded):
    if expanded:
        self.filter_expander.setArrowType(Qt.DownArrow)
        self.filter_content.setVisible(expanded)
        self.filter_scroll.setVisible(expanded)
        self.filter_status.setVisible(expanded)
        self.render_count.setVisible(expanded)
        self.filter_action_buttons.setVisible(expanded)
        return None
    else:
        self.filter_expander.setArrowType(Qt.RightArrow)
        self.filter_content.setVisible(expanded)
        self.filter_scroll.setVisible(expanded)
        self.filter_status.setVisible(expanded)
        self.render_count.setVisible(expanded)
        self.filter_action_buttons.setVisible(expanded)
        return None
