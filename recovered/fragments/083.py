# Source Generated with Decompyle++
# File: 083.pyc (Python 3.10)

self.region_expander.setArrowType(Qt.DownArrow if expanded else Qt.RightArrow)
self.region_scroll.setVisible(expanded)
if not expanded:
    self.cancel_point_edit_mode()
    return None
