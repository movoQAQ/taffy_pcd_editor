#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
ctx=$(mktemp -d)
trap 'rm -rf "$ctx"' EXIT
cp "$(command -v uv)" "$ctx/uv"
cp docker/Dockerfile.runtime "$ctx/Dockerfile"
docker build --secret id=proxy_ca,src=/etc/ssl/certs/ca-certificates.crt -t taffy-runtime:ubuntu24.04 "$ctx"
