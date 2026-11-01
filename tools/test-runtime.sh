#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
docker run --rm --network none --user "$(id -u):$(id -g)" -e HOME=/tmp -e QT_QPA_PLATFORM=offscreen -v "$PWD:/work" taffy-runtime:ubuntu24.04 python -m pytest -q -p no:cacheprovider tests/test_runtime.py
docker run --rm --network none --user "$(id -u):$(id -g)" -e HOME=/tmp -e LIBGL_ALWAYS_SOFTWARE=1 -v "$PWD:/work" taffy-runtime:ubuntu24.04 timeout 45 xvfb-run -a python tests/startup_smoke.py
