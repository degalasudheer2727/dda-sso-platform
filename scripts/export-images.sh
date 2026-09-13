#!/bin/sh
# Run on the connected machine after building the derived images.
set -eu
cd "$(dirname "$0")/.."
mkdir -p .runtime/airgap
# Give upstream images the deterministic names used by import-images.sh.
docker image inspect dda/dex:v2.45.1 > /dev/null # Built with dex/Dockerfile; never replace with the unmodified upstream tag.
docker tag quay.io/sclorg/postgresql-16-c9s@sha256:fbef891ec464ee8d20332c7f9a4a68decc0b6db8460e7e875df6f33cac5003dc dda/postgresql:16
docker save -o .runtime/airgap/dda-images.tar dda/dex:v2.45.1 dda/postgresql:16 dda/keycloak:26.7.3 dda/open-webui:v0.11.3
shasum -a 256 .runtime/airgap/dda-images.tar > .runtime/airgap/dda-images.tar.sha256
printf 'Created .runtime/airgap/dda-images.tar and SHA256 checksum\n'
