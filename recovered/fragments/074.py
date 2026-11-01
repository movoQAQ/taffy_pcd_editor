# Source Generated with Decompyle++
# File: 074.pyc (Python 3.10)

if any((lambda .0: for worker in .0:
worker.isRunning())(self.task_workers)):
    QMessageBox.information(self, '任务运行中', '后台任务尚未完成，请完成后再关闭窗口。')
    event.ignore()
    return None
None.rotate_timer.stop()
self.visible_stats_timer.stop()
self.vtk_widget.Finalize()
event.accept()
