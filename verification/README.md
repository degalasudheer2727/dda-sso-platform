# Verification evidence

Local Mac, Docker Desktop, linux/amd64 containers. Tested 2026-09-13/14.

- Five direct browser logins: Web UI → Dex (via Keycloak hint) → Web UI, without a second profile form.
- Dedicated administrator first login also completed without profile review; later role refresh exposed Admin Panel.
- Same administrator SSO session opened the Keycloak dda administration console without another password.
- Five ordinary roles retained; dedicated administrator granted realm-admin and webui-admin explicitly.
- Keycloak rejected an unregistered redirect URI (HTTP 400).
- Dex, Keycloak, database and Web UI have been restarted/recreated while identities and app users persisted.
- Derived Web UI image started healthy as UID 1000710000:GID 0; Keycloak optimized image build and arbitrary-UID path permissions checked.
- 27 native manifests pass relationship/security checks and Kustomize rendering.
- Offline runtime image archive created with SHA256 checksum.

`local-results.json` records API/database checks. Local-only screenshots show the direct upstream login, ordinary Web UI, administrator menu and Keycloak console. Authenticated screenshots and video are excluded from Git/GitHub. The repository contains only this sanitized report and source diagrams. `profile.png` is an earlier diagnostic from before seamless profile provisioning and is not final-demo evidence.

Not performed: admission/deployment on an enterprise OpenShift cluster, cluster TLS/SCC/storage/NetworkPolicy tests, HA/failure-load tests, or an enterprise LLM/RAG connection. The backup script is exercised locally; a full restore drill remains a production gate.
