#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
if [[ ! -x "$ROOT_DIR/taffy-pcd-editor" ]]; then
    "$ROOT_DIR/build.sh"
fi
exec "$ROOT_DIR/taffy-pcd-editor" "$@"
