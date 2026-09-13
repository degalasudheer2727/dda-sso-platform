#!/bin/sh
# On an air-gapped Linux transfer host with podman and access to the internal registry.
set -eu
: "${1:?Usage: import-images.sh registry.example.internal/dda /path/to/dda-images.tar}"
: "${2:?Provide the image archive path}"
registry=${1%/}
podman load -i "$2"
for item in dex:v2.45.1 postgresql:16 keycloak:26.7.3 open-webui:v0.11.3; do
  source="docker.io/dda/$item"
  case "$item" in
    keycloak:*) target="$registry/keycloak-dda:26.7.3" ;;
    open-webui:*) target="$registry/open-webui-dda:v0.11.3" ;;
    *) target="$registry/$item" ;;
  esac
  podman tag "$source" "$target"
  podman push "$target"
done
