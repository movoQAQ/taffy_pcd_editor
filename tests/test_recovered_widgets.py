"""Compare Qt input, signal and paint behavior against the release widgets."""
import pytest
from PyQt5.QtCore import QEvent, QPoint, QPointF, Qt
from PyQt5.QtGui import QMouseEvent, QWheelEvent
from PyQt5.QtTest import QSignalSpy, QTest
from PyQt5.QtWidgets import QApplication, QStyle, QStyleOptionSlider
from recovered.source import widgets
from test_runtime import app_module


@pytest.fixture(scope='module')
def qt_app():
    app = QApplication.instance() or QApplication([])
    return app


@pytest.mark.parametrize('orientation', [Qt.Horizontal, Qt.Vertical])
def test_range_input_and_paint(qt_app, app_module, orientation):
    results = []
    images = []
    for cls in (app_module.HeightRangeSlider, widgets.HeightRangeSlider):
        slider = cls(orientation)
        slider.resize(300, 240)
        slider.show()
        spy = QSignalSpy(slider.rangeChanged)
        slider.set_range(100, 900)
        assert len(spy) == 0
        QTest.keyClick(slider, Qt.Key_Right)
        assert slider.low == 110
        slider.dragging = 'high'
        QTest.keyClick(slider, Qt.Key_Left)
        assert slider.high == 890
        coordinate = round(slider._y(250))
        pos = QPoint(slider.width() // 2, coordinate) if orientation == Qt.Vertical else QPoint(coordinate, slider.height() // 2)
        QTest.mousePress(slider, Qt.LeftButton, pos=pos)
        coordinate = round(slider._y(600))
        pos = QPoint(slider.width() // 2, coordinate) if orientation == Qt.Vertical else QPoint(coordinate, slider.height() // 2)
        qt_app.sendEvent(slider, QMouseEvent(QEvent.MouseMove, QPointF(pos), Qt.NoButton, Qt.LeftButton, Qt.NoModifier))
        QTest.mouseRelease(slider, Qt.LeftButton, pos=pos)
        assert abs(slider.low - 600) <= 3 and slider.dragging is None
        QTest.qWait(20)
        images.append(slider.grab().toImage())
        results.append((slider.low, slider.high, list(spy), [slider._value(p) for p in (-100, 0, 50, 1000)]))
        slider.close()
    assert results[0] == results[1]
    assert images[0] == images[1]


@pytest.mark.parametrize('orientation', [Qt.Horizontal, Qt.Vertical])
def test_drag_only_slider(qt_app, app_module, orientation):
    results = []
    for cls in (app_module.DragOnlySlider, widgets.DragOnlySlider):
        slider = cls(orientation)
        slider.resize(240, 40) if orientation == Qt.Horizontal else slider.resize(40, 240)
        slider.setRange(0, 100)
        slider.setValue(50)
        slider.show()
        QTest.mouseClick(slider, Qt.LeftButton, pos=QPoint(2, 2))
        assert slider.value() == 50
        wheel = QWheelEvent(QPointF(10, 10), QPointF(10, 10), QPoint(), QPoint(0, 120), Qt.NoButton, Qt.NoModifier, Qt.NoScrollPhase, False)
        qt_app.sendEvent(slider, wheel)
        assert slider.value() == 50 and not wheel.isAccepted()
        option = QStyleOptionSlider()
        slider.initStyleOption(option)
        handle = slider.style().subControlRect(QStyle.CC_Slider, option, QStyle.SC_SliderHandle, slider)
        QTest.mousePress(slider, Qt.LeftButton, pos=handle.center())
        assert slider._dragging_handle
        pos = handle.center() + (QPoint(40, 0) if orientation == Qt.Horizontal else QPoint(0, -40))
        qt_app.sendEvent(slider, QMouseEvent(QEvent.MouseMove, QPointF(pos), Qt.NoButton, Qt.LeftButton, Qt.NoModifier))
        QTest.mouseRelease(slider, Qt.LeftButton, pos=pos)
        assert slider.value() > 50 and not slider._dragging_handle
        results.append(slider.value())
        slider.close()
    assert results[0] == results[1]
