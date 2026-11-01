#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p analysis recovered
# Runs static analysis tools only; never imports or executes the application.
docker run --rm --network none --user "$(id -u):$(id -g)" -v "$PWD:/work" taffy-recovery:ubuntu24.04 bash -c '
pycdas original/rootfs/opt/taffy-editor/main.pyc > analysis/main.disassembly.txt 2> analysis/disassembly.stderr.txt
a=$?
pycdc original/rootfs/opt/taffy-editor/main.pyc > recovered/main.py 2> analysis/decompiler.stderr.txt
b=$?
printf "pycdas exit: %s\npycdc exit: %s\n" "$a" "$b" > analysis/tool-status.txt
exit "$a"
'
