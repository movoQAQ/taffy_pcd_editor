#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
: "${DISPLAY:?Run this command from a Linux X11 desktop with DISPLAY set}"
test -x .venv/bin/python || { echo 'Run tools/setup-local.sh first.' >&2; exit 1; }
export LIBGL_ALWAYS_SOFTWARE=${LIBGL_ALWAYS_SOFTWARE:-1}
exec .venv/bin/python -E -s tools/run_editor.py "$@"
