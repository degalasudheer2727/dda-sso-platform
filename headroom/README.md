# Headroom — local Codex utility

The existing Headroom service is retained in `compose.yaml` on loopback port 8787. It is independent of the Dex/Keycloak/Open WebUI identity chain and is not required for SSO. It is intentionally excluded from the enterprise SSO image bundle and OpenShift resources.

See `../HEADROOM.md` for the existing Codex routing and rollback instructions. Do not copy a developer's Codex authentication state into enterprise containers.
