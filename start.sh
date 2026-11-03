#!/usr/bin/env bash
set -euo pipefail
project_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
cd "$project_root"

case "${1:-}" in
    -h|--help) ;;
    *) : "${DISPLAY:?请从 Linux 图形桌面的终端启动，需要 DISPLAY。}" ;;
esac

if [ ! -x .venv/bin/python ]; then
    echo '首次启动：正在配置本机 Python 3.10 环境…'
    ./tools/setup-local.sh
fi
export LIBGL_ALWAYS_SOFTWARE=${LIBGL_ALWAYS_SOFTWARE:-1}
exec .venv/bin/python -E -s tools/run_editor.py "$@"
