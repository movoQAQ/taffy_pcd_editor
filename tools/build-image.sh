#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")/.." && pwd)
ctx=$(mktemp -d)
trap 'rm -rf "$ctx"' EXIT
 git clone https://github.com/zrax/pycdc.git "$ctx/pycdc"
git -C "$ctx/pycdc" checkout --detach b4289760970dbc399684f1e155ec6d1ea1cc787e
cp "$root/docker/Dockerfile" "$ctx/Dockerfile"
docker build --secret id=proxy_ca,src=/etc/ssl/certs/ca-certificates.crt -t taffy-recovery:ubuntu24.04 "$ctx"
