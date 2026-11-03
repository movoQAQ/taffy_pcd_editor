"""Desktop Qt/VTK workflow checks, run once per original/integrated module.

File dialogs use temporary paths. Region geometry is deterministic test input;
the deletion/completion buttons and background workers are real.
"""
import json
import os
from pathlib import Path
import sys
import time

import numpy as np
import pytest
from PyQt5.QtCore import QCoreApplication, QEvent, QPoint, Qt
from PyQt5.QtGui import QFont
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication, QPushButton
from vtkmodules.util.numpy_support import vtk_to_numpy

from tools.run_editor import ROOT, load_editor


def wait_until(predicate, timeout=15000):
    deadline = time.monotonic() + timeout / 1000
    while not predicate():
        assert time.monotonic() < deadline, 'Timed out waiting for Qt background operation'
        QTest.qWait(20)
    QTest.qWait(50)


def close_window(window, timeout=15000):
    # closeEvent also waits for visible-count workers, unlike _editing_busy.
    wait_until(lambda: not any(worker.isRunning() for worker in window.task_workers), timeout)
    assert window.close(), 'Window refused to close after background tasks finished'
    assert not window.isVisible()
    # Release Qt signal closures and VTK objects before the next parametrized case.
    window.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
    QTest.qWait(100)


def click(window, text):
    matches = [b for b in window.findChildren(QPushButton) if b.text() == text]
    assert len(matches) == 1, (text, [b.text() for b in window.findChildren(QPushButton)])
    button = matches[0]
    assert button.isEnabled() and button.isVisible(), text
    if window.region_content.isAncestorOf(button):
        window.region_scroll.ensureWidgetVisible(button)
        QTest.qWait(20)
    QTest.mouseClick(button, Qt.LeftButton)
    QTest.qWait(30)


@pytest.fixture(scope='module')
def qt_app():
    app = QApplication.instance() or QApplication([])
    app.setFont(QFont('Noto Sans CJK SC', 10))
    return app


@pytest.mark.parametrize('variant', ['original', 'recovered'])
def test_desktop_workflow(qt_app, monkeypatch, tmp_path, variant):
    assert qt_app.platformName() != 'offscreen', 'Use X11/Xvfb for the VTK integration test'
    module = load_editor(use_recovered=variant == 'recovered')
    qt_app.setStyleSheet(module.APP_STYLE)
    exceptions, dialogs = [], []
    monkeypatch.setattr(sys, 'excepthook', lambda typ, value, tb: exceptions.append(repr(value)))
    for name in ('warning', 'critical', 'information'):
        monkeypatch.setattr(module.QMessageBox, name, lambda parent, title, message, *a, **k: dialogs.append((title, message)))
    artifacts = Path(os.environ.get('TAFFY_UI_ARTIFACT_DIR', ROOT / 'analysis/ui'))
    artifacts.mkdir(parents=True, exist_ok=True)
    report = {'variant': variant, 'platform': qt_app.platformName(), 'checks': []}
    window = module.PointCloudWindow()
    window.show()
    QTest.qWait(300)
    try:
        assert window.isVisible() and window.points is None
        assert window.metric_points.text() == '0'
        if variant == 'recovered':
            assert type(window.z_range_slider).__module__ == 'recovered.source.widgets'
            assert module.load_pcd_data.__module__ == 'recovered.source.core'
        report['checks'].append('empty startup')

        points = module.make_demo_cloud()
        path = tmp_path / 'demo.pcd'
        module.write_full_pcd(path, points)
        monkeypatch.setattr(module.QFileDialog, 'getOpenFileName', lambda *a, **k: (str(path), ''))
        click(window, '＋   导入 PCD 文件')
        wait_until(lambda: len(window.layers) == 1 and 'edit_points' in window.layers[0] and not window._editing_busy())
        np.testing.assert_array_equal(window.current_full_points(), points)
        assert window.total_points == len(points)
        report['imported_points'] = len(points)
        report['checks'].append('import button and asynchronous full load')
        QTest.qWait(250)

        window.vtk_widget.GetRenderWindow().Render()
        capture = module.vtk.vtkWindowToImageFilter()
        capture.SetInput(window.vtk_widget.GetRenderWindow())
        capture.SetInputBufferTypeToRGB()
        capture.ReadFrontBufferOff()
        capture.Update()
        colors = vtk_to_numpy(capture.GetOutput().GetPointData().GetScalars())
        assert len(np.unique(colors, axis=0)) > 100, 'VTK viewport appears blank'
        writer = module.vtk.vtkPNGWriter()
        writer.SetFileName(str(artifacts / f'{variant}-viewport.png'))
        writer.SetInputConnection(capture.GetOutputPort())
        writer.Write()
        # QWidget.grab() cannot capture the native VTK/OpenGL child reliably.
        assert window.screen().grabWindow(int(window.winId())).save(str(artifacts / f'{variant}-window.png'))
        report['checks'].append('nonblank VTK rendering and screenshot')

        slider = window.x_range_slider
        slider.setFocus()
        QTest.keyClick(slider, Qt.Key_Right)
        assert slider.low == 10
        assert window.axis_ranges['x'][0] > window.axis_bounds['x'][0]
        QTest.mouseClick(slider, Qt.LeftButton, pos=QPoint(slider.width() // 2, round(slider._y(400))))
        assert 390 <= slider.low <= 410
        visible = window.current_visible_full_points()
        assert 0 < len(visible) < len(points)
        click(window, '重置')
        assert window.x_range_slider.low == 0 and window.x_range_slider.high == 1000
        report['checks'].append('range keyboard/mouse input and reset')

        click(window, '网格 ✓')
        assert not window.grid_actor.GetVisibility()
        click(window, '网格 ✓')
        click(window, '俯视')
        camera = window.renderer.GetActiveCamera()
        before = camera.GetParallelProjection()
        click(window, '透视')
        assert camera.GetParallelProjection() != before
        click(window, '透视')
        layer = window.layers[0]
        QTest.mouseClick(layer['eye'], Qt.LeftButton)
        assert not layer['actor'].GetVisibility()
        QTest.mouseClick(layer['eye'], Qt.LeftButton)
        assert layer['actor'].GetVisibility()
        report['checks'].append('grid, top view, projection and layer visibility')

        QTest.mouseClick(window.filter_expander, Qt.LeftButton)
        QTest.mouseClick(window.filter_enabled, Qt.LeftButton, pos=QPoint(8, window.filter_enabled.height() // 2))
        assert window.filter_enabled.isChecked()
        window.voxel_slider.setValue(15)
        window.write_filtered.setChecked(False)
        click(window, '重新计算滤波')
        wait_until(lambda: not window._editing_busy() and '滤波结果为空' in window.filter_status.text())
        np.testing.assert_array_equal(window.current_full_points(), points)
        report['checks'].append('empty filter result preserves source points')
        if window.filter_result_popup:
            window.filter_result_popup.close()
        # The demo spans 84 m: the release's 5 cm / 20-neighbor defaults
        # reject all points. Use a 1 m / 2-neighbor radius for this fixture.
        window.filter_parameter_sliders['radius_size'][0].setValue(100)
        window.filter_parameter_sliders['radius_neighbors'][0].setValue(2)
        click(window, '重新计算滤波')
        wait_until(lambda: not window._editing_busy() and '滤波结果已写回' in window.filter_status.text())
        filtered = window.current_full_points().copy()
        assert 0 < len(filtered) < len(points)
        report['filtered_points'] = len(filtered)
        report['checks'].append('filter button and background result')
        if window.filter_result_popup:
            window.filter_result_popup.close()
        QTest.qWait(50)
        # Committing a filter result resets this checkbox in the release.
        assert not window.filter_enabled.isChecked()

        # Restore the fixture before testing region edits independently of filtering.
        window._replace_active_source_points(points.copy())
        click(window, '重置')
        wait_until(lambda: not window._editing_busy())
        QTest.mouseClick(window.region_expander, Qt.LeftButton)
        click(window, '开始选点区域')
        assert window.point_edit_mode == 'delete'
        pick = points[np.argmax(points[:, 2])]
        window.renderer.SetWorldPoint(*pick, 1.0)
        window.renderer.WorldToDisplay()
        x, y, _ = window.renderer.GetDisplayPoint()
        width, height = window.vtk_widget.GetRenderWindow().GetSize()
        pos = QPoint(round(x * window.vtk_widget.width() / width),
                     round(window.vtk_widget.height() - 1 - y * window.vtk_widget.height() / height))
        assert window.vtk_widget.rect().contains(pos)
        QTest.mouseDClick(window.vtk_widget, Qt.LeftButton, pos=pos)
        QTest.qWait(50)
        assert len(window.region_pick_points) == 1
        report['checks'].append('double-click point picking in VTK viewport')
        vertices = np.array([[x, y, z] for x in (-30, -18) for y in (-24, -10) for z in (0, 10)], dtype=float)
        window.region_pick_points[:] = list(vertices)
        window.filter_parameter_sliders['region_expand'][0].setValue(0)
        click(window, '计算凸包区域')
        assert window.selected_hull_equations is not None and window.region_preview_actor is not None
        equations = window.selected_hull_equations.copy()
        bounds = window.selected_region_vertices.min(0), window.selected_region_vertices.max(0)
        mask = module.points_inside_region(points, equations, bounds, np.array([window.axis_ranges[a] for a in 'xyz']))
        assert 0 < mask.sum() < len(points)
        QTest.mouseClick(window.delete_region_button, Qt.LeftButton)
        wait_until(lambda: not window._editing_busy() and '已删除' in window.region_pick_status.text())
        np.testing.assert_array_equal(window.current_full_points(), points[~mask])
        report['deleted_points'] = int(mask.sum())
        report['checks'].append('hull preview and delete button with deterministic vertices')

        window.filter_parameter_sliders['completion_spacing'][0].setValue(50)
        window.region_scroll.ensureWidgetVisible(window.complete_region_button)
        QTest.mouseClick(window.complete_region_button, Qt.LeftButton)
        wait_until(lambda: not window._editing_busy() and '已补全' in window.region_pick_status.text())
        completed = window.current_full_points().copy()
        assert len(completed) > (~mask).sum()
        np.testing.assert_array_equal(completed[:(~mask).sum()], points[~mask])
        report['added_points'] = int(len(completed) - (~mask).sum())
        report['checks'].append('completion button and background result')

        exported = tmp_path / 'exported.pcd'
        monkeypatch.setattr(module.QFileDialog, 'getSaveFileName', lambda *a, **k: (str(exported), ''))
        window.export_layer(window.active_layer_id)
        wait_until(lambda: exported.exists() and not window._editing_busy())
        np.testing.assert_array_equal(module.load_full_xyz(exported), completed)
        assert path.read_bytes() != exported.read_bytes()
        np.testing.assert_array_equal(module.load_full_xyz(path), points)
        report['checks'].append('edited PCD export and original file preserved')
        report['qt_exceptions'] = exceptions
        report['unexpected_dialogs'] = dialogs
    finally:
        if sys.exc_info()[0] is not None:
            print('UI failure state:', window.filter_status.text(), window.region_pick_status.text(), exceptions, dialogs)
        close_window(window)
    assert not exceptions, exceptions
    assert not dialogs, dialogs
    report['checks'].append('clean close')
    (artifacts / f'{variant}-report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
