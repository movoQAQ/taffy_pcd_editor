#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
: "${DISPLAY:?Run this command from a Linux X11 desktop with DISPLAY set}"
auth=${XAUTHORITY:-$HOME/.Xauthority}
test -f "$auth" || { echo 'An Xauthority cookie file is required; set XAUTHORITY.' >&2; exit 1; }
docker run --rm --network none --user "$(id -u):$(id -g)" -e DISPLAY -e HOME=/tmp -e XAUTHORITY=/tmp/taffy.xauth -e LIBGL_ALWAYS_SOFTWARE=1 -v "$auth:/tmp/taffy.xauth:ro" -v /tmp/.X11-unix:/tmp/.X11-unix:ro -v "$PWD:/work" taffy-runtime:ubuntu24.04
