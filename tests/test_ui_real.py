"""Optional real-data validation: TAFFY_TEST_PCD=/path/map.pcd pytest this file.

The input is read-only; all exported PCDs go to pytest's temporary directory.
"""
import hashlib
import json
import os
from pathlib import Path
import sys
import time

import numpy as np
import pytest
from PyQt5.QtCore import QPoint, Qt
from PyQt5.QtTest import QTest

from test_ui import click, close_window, qt_app, wait_until
from tools.run_editor import ROOT, load_editor


@pytest.mark.skipif(not os.environ.get('TAFFY_TEST_PCD'), reason='Set TAFFY_TEST_PCD to a local PCD for real-data validation')
@pytest.mark.parametrize('variant', ['original', 'recovered'])
def test_real_pcd(qt_app, monkeypatch, tmp_path, variant):
    path = Path(os.environ['TAFFY_TEST_PCD']).resolve(strict=True)
    original_hash = hashlib.sha256(path.read_bytes()).hexdigest()
    module = load_editor(variant == 'recovered')
    reference = load_editor(False)
    expected = reference.load_full_xyz(path)
    full = module.load_full_xyz(path)
    np.testing.assert_array_equal(full, expected)
    assert full.strides == expected.strides
    assert np.isfinite(full).all()
    qt_app.setStyleSheet(module.APP_STYLE)
    exceptions, dialogs = [], []
    monkeypatch.setattr(sys, 'excepthook', lambda typ, value, tb: exceptions.append(repr(value)))
    for name in ('warning', 'critical', 'information'):
        monkeypatch.setattr(module.QMessageBox, name, lambda parent, title, message, *a, **k: dialogs.append((title, message)))
    report = {'variant': variant, 'file': str(path), 'input_sha256': original_hash,
              'input_points': len(full), 'xyz_strides': list(full.strides), 'checks': []}
    artifacts = Path(os.environ.get('TAFFY_UI_ARTIFACT_DIR', ROOT / 'analysis/ui'))
    artifacts.mkdir(parents=True, exist_ok=True)
    window = module.PointCloudWindow()
    window.show()
    QTest.qWait(200)
    try:
        monkeypatch.setattr(module.QFileDialog, 'getOpenFileName', lambda *a, **k: (str(path), ''))
        started = time.monotonic()
        click(window, '＋   导入 PCD 文件')
        wait_until(lambda: len(window.layers) == 1 and 'edit_points' in window.layers[0] and not window._editing_busy(), 30000)
        report['import_seconds'] = round(time.monotonic() - started, 3)
        np.testing.assert_array_equal(window.current_full_points(), full)
        assert window.total_points == len(full)
        QTest.qWait(250)
        report['render_points'] = len(window.points)
        assert window.screen().grabWindow(int(window.winId())).save(str(artifacts / f'rmuc-{variant}-window.png'))
        report['checks'].append('real PCD import, full load and original/source array equality')

        slider = window.x_range_slider
        QTest.mouseClick(slider, Qt.LeftButton, pos=QPoint(slider.width() // 2, round(slider._y(200))))
        QTest.qWait(250)
        mask = module.range_mask(full, window.axis_ranges)
        assert 0 < mask.sum() < len(full)
        report['range_points'] = int(mask.sum())
        report['checks'].append('range slider on real points')

        QTest.mouseClick(window.filter_expander, Qt.LeftButton)
        window.statistical_filter.setChecked(False)
        window.radius_filter.setChecked(False)
        window.voxel_slider.setValue(5)
        QTest.mouseClick(window.filter_enabled, Qt.LeftButton, pos=QPoint(8, window.filter_enabled.height() // 2))
        assert window.filter_enabled.isChecked()
        started = time.monotonic()
        click(window, '重新计算滤波')
        wait_until(lambda: not window._editing_busy() and '滤波结果已写回' in window.filter_status.text(), 30000)
        filtered = window.current_full_points()
        assert 0 < len(filtered) < len(full)
        # DisplayFilterWorker must retain every out-of-range source point.
        np.testing.assert_array_equal(filtered[:int((~mask).sum())], full[~mask])
        report['filter_seconds'] = round(time.monotonic() - started, 3)
        report['filtered_points'] = len(filtered)
        report['checks'].append('5 cm voxel filtering preserves out-of-range points')
        if window.filter_result_popup:
            window.filter_result_popup.close()
        QTest.qWait(50)

        window._replace_active_source_points(full.copy())
        click(window, '重置')
        QTest.mouseClick(window.filter_expander, Qt.LeftButton)
        QTest.mouseClick(window.region_expander, Qt.LeftButton)
        click(window, '开始选点区域')
        center = full[len(full) // 3]
        low = np.maximum(full.min(0), center - 0.25)
        high = np.minimum(full.max(0), center + 0.25)
        vertices = np.array([[x, y, z] for x in (low[0], high[0])
                             for y in (low[1], high[1]) for z in (low[2], high[2])])
        window.region_pick_points[:] = list(vertices)
        window.filter_parameter_sliders['region_expand'][0].setValue(0)
        click(window, '计算凸包区域')
        assert window.selected_hull_equations is not None
        bounds = window.selected_region_vertices.min(0), window.selected_region_vertices.max(0)
        mask = module.points_inside_region(full, window.selected_hull_equations, bounds,
                                           np.array([window.axis_ranges[a] for a in 'xyz']))
        assert 0 < mask.sum() < len(full)
        QTest.mouseClick(window.delete_region_button, Qt.LeftButton)
        wait_until(lambda: not window._editing_busy() and '已删除' in window.region_pick_status.text(), 30000)
        np.testing.assert_array_equal(window.current_full_points(), full[~mask])
        report['deleted_points'] = int(mask.sum())
        report['checks'].append('region delete matches geometric mask for full cloud')

        window.filter_parameter_sliders['completion_spacing'][0].setValue(5)
        window.region_scroll.ensureWidgetVisible(window.complete_region_button)
        QTest.qWait(20)
        QTest.mouseClick(window.complete_region_button, Qt.LeftButton)
        wait_until(lambda: not window._editing_busy() and '已补全' in window.region_pick_status.text(), 30000)
        completed = window.current_full_points()
        report['added_points'] = int(len(completed) - (~mask).sum())
        assert report['added_points'] > 0
        np.testing.assert_array_equal(completed[:int((~mask).sum())], full[~mask])
        report['checks'].append('region completion preserves remaining source points')
        exported = tmp_path / 'rmuc-edited.pcd'
        monkeypatch.setattr(module.QFileDialog, 'getSaveFileName', lambda *a, **k: (str(exported), ''))
        window.export_layer(window.active_layer_id)
        wait_until(lambda: exported.exists() and not window._editing_busy(), 30000)
        np.testing.assert_array_equal(reference.load_full_xyz(exported), completed)
        report['export_points'] = len(completed)
        report['export_fields'] = ['x', 'y', 'z']
        report['checks'].append('edited XYZ export roundtrip')
    finally:
        if sys.exc_info()[0] is not None:
            print('UI failure state:', window.filter_status.text(), window.region_pick_status.text(), exceptions, dialogs)
            print('UI import requests/active layer:', window.full_load_request, window.active_layer_id,
                  [layer['id'] for layer in window.layers])
            print('UI layers/workers:', len(window.layers), [list(layer) for layer in window.layers],
                  [(type(worker).__name__, worker.isRunning(), worker is window.visible_count_worker)
                   for worker in window.task_workers])
        close_window(window, 30000)
        assert hashlib.sha256(path.read_bytes()).hexdigest() == original_hash
    assert not dialogs, dialogs
    assert not exceptions, exceptions
    report['checks'].append('clean close and unchanged input SHA-256')
    report['qt_exceptions'] = exceptions
    report['unexpected_dialogs'] = dialogs
    (artifacts / f'rmuc-{variant}-report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
