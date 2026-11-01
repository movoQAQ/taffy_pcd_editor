def _visible_count_finished(self, worker):
    if self.visible_count_worker is worker:
        self.visible_count_worker = None
        if self.render_source_points is not None:
            if self.visible_count_request != worker.request_id:
                QTimer.singleShot(0, self._update_visible_stats)
                return None
                return None
                return None
        else:
            return None
    else:
        return None
        return None
    return None
