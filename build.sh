#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
if ! command -v cargo >/dev/null 2>&1; then
    if [[ -f "$HOME/.cargo/env" ]]; then source "$HOME/.cargo/env"; fi
fi
cd -- "$ROOT_DIR"
cargo build --locked --release
install -m 755 target/release/taffy-pcd-editor taffy-pcd-editor
printf 'Built: %s/taffy-pcd-editor\n' "$ROOT_DIR"
