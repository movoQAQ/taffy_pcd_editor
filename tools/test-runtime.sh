#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
test -x .venv/bin/python || { echo 'Run tools/setup-local.sh first.' >&2; exit 1; }
export PYTEST_DISABLE_PLUGIN_AUTOLOAD=1
export OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2
QT_QPA_PLATFORM=offscreen .venv/bin/python -E -s -m pytest -q -p no:cacheprovider tests/test_runtime.py tests/test_recovered_source.py tests/test_recovered_widgets.py
: "${DISPLAY:?UI tests require a desktop display or xvfb-run}"
export LIBGL_ALWAYS_SOFTWARE=${LIBGL_ALWAYS_SOFTWARE:-1}
QT_QPA_PLATFORM=xcb timeout 120 .venv/bin/python -E -s -m pytest -q -p no:cacheprovider tests/test_ui.py
if [ -n "${TAFFY_TEST_PCD:-}" ]; then
    QT_QPA_PLATFORM=xcb timeout 180 .venv/bin/python -E -s -m pytest -q -p no:cacheprovider tests/test_ui_real.py
fi
