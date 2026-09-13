# Headroom for Codex

The installed Headroom v0.27.0 image is pinned by digest in `compose.yaml`. The proxy listens on `127.0.0.1:8787`, uses token mode, and restarts with Docker Desktop. Codex model routing and its Docker-backed Headroom MCP entry are configured in `~/.codex/config.toml`.

Restart Codex to reload provider and MCP settings. Headroom processes model requests locally before forwarding them to the provider with Codex's existing authentication. The MCP tool can retrieve originals from compression markers. Automatic injection of extra retrieval tools is disabled because retrieval is already registered through MCP.

```sh
docker compose up -d headroom
curl http://127.0.0.1:8787/health
curl http://127.0.0.1:8787/stats
```

The proxy dashboard is at http://localhost:8787. Savings depend on workload; short requests and protected prompt content may not shrink. On-demand MCP compression after content has entered context does not undo already consumed tokens.

Codex's previous configuration was backed up at `~/.codex/config.toml.before-headroom-20260913`. To undo routing, remove the marked top-level Headroom routing block and `[model_providers.headroom]` table, then restart Codex. The previous stopped proxy is retained as `headroom-proxy-before-codex`.
