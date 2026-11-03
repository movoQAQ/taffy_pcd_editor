"""Headless startup/event-loop check; no interaction or UI feature assertions."""
import runpy
from pathlib import Path
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer
p = Path(__file__).resolve().parents[1] / 'original/main.pyc'
m = runpy.run_path(str(p), run_name='taffy_smoke')
app = QApplication([])
window = m['PointCloudWindow']()
window.show()
ticks = []
timer = QTimer()
timer.timeout.connect(lambda: ticks.append(1))
timer.start(100)
QTimer.singleShot(5000, app.quit)
app.exec_()
assert len(ticks) >= 20, f'Event loop stalled: {len(ticks)} ticks'
window.close()
print(f'STARTUP_OK: {len(ticks)} event-loop ticks')
