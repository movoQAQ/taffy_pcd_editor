#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
if command -v uv >/dev/null 2>&1; then
    uv_bin=$(command -v uv)
else
    if [ ! -x .bootstrap/bin/uv ]; then
        python3 -m venv .bootstrap
        .bootstrap/bin/python -m pip install --disable-pip-version-check --no-cache-dir 'uv==0.13.7'
    fi
    uv_bin=$PWD/.bootstrap/bin/uv
fi
if [ ! -x .venv/bin/python ]; then
    "$uv_bin" venv --python 3.10 .venv
fi
.venv/bin/python -E -s -c 'import sys; assert sys.version_info[:2] == (3, 10), "The original bytecode requires Python 3.10"'
"$uv_bin" pip install --python .venv/bin/python --no-cache -r tools/requirements-runtime.txt
.venv/bin/python -E -s -c 'import numpy, scipy, PyQt5.QtWidgets, vtk, open3d; print("Local runtime ready")'
