#!/bin/sh
# Quiesces SQLite writers. Brief outage; services restart automatically on exit.
set -eu
cd "$(dirname "$0")/.."
stamp=$(date -u +%Y%m%dT%H%M%SZ)
dest="backups/identity-$stamp"
mkdir -p "$dest"
chmod 700 "$dest"
trap 'scripts/local.sh start dex keycloak open-webui' EXIT
scripts/local.sh stop open-webui dex keycloak
docker exec dda-keycloak-db pg_dump -U keycloak keycloak > "$dest/keycloak.sql"
docker cp dda-dex:/var/dex/. "$dest/dex"
docker cp open-webui:/app/backend/data/. "$dest/open-webui"
cp -R .runtime/dex .runtime/keycloak .runtime/secrets.json .runtime/identity.env "$dest/"
printf 'Backup saved to %s\n' "$dest"
