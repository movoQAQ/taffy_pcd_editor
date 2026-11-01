def _filter_worker_finished(self, worker):
    if self.filter_worker is worker:
        self.filter_worker = None
        if self.filter_enabled.isChecked():
            if self.filter_recalculate_requested:
                QTimer.singleShot(0, self.start_display_filter)
                return None
                return None
                return None
        else:
            return None
    else:
        return None
        return None
    return None
