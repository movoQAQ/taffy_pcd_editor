def closeEvent(self, event):
    """original function name <genexpr> is illegal, use a temp name."""
    
    
    def __temp_5900(comp_arg_0):
        for __temp_5901 in comp_arg_0:
            worker = __temp_5901
            yield worker.isRunning()
            continue
        return None
    
    
    if any(__temp_5900(iter(self.task_workers))):
        QMessageBox.information(self, '任务运行中', '后台任务尚未完成，请完成后再关闭窗口。')
        event.ignore()
        return None
    self.rotate_timer.stop()
    self.visible_stats_timer.stop()
    self.vtk_widget.Finalize()
    event.accept()
    return None
