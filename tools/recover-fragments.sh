#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
test -f analysis/code-objects/000.pyc
docker run --rm --network none --user "$(id -u):$(id -g)" -v "$PWD:/work" taffy-recovery:ubuntu24.04 bash -c 'mkdir -p recovered/fragments analysis/fragments; for f in analysis/code-objects/*.pyc; do n=$(basename "$f" .pyc); timeout 5 pycdc "$f" > "recovered/fragments/$n.py" 2> "analysis/fragments/$n.stderr.txt"; echo "$n $?"; done' > analysis/fragment-status.txt
