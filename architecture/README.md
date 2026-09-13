# Architecture diagrams

Open `dda-sso-architecture.drawio` in diagrams.net / Draw.io Desktop. It is an uncompressed, editable four-page document; every service, label, container and connector remains editable. No passwords or client secrets are included.

1. `01-local.svg` — deployed Mac topology, versions, ports, Docker aliases, persistent data, Headroom isolation, source and backup boundaries.
2. `02-sso.svg` — direct Dex login, authorization-code exchanges, PKCE, profile inheritance, user/admin roles and session boundaries.
3. `03-openshift.svg` — disconnected image transfer, internal registry, Routes, Deployments, PVCs, Secrets, network/runtime controls and production validation gates. This page is explicitly a reference, not a claim that the cluster was deployed.
4. `04-operations.svg` — complete identity inventory, administration methods, private material, evidence and enterprise handoff boundaries.

Rebuild both formats with `python3 scripts/build-architecture.py`. The Draw.io file and SVGs are generated from the same layout/source in that script, preventing topology drift between formats. OpenShift details correspond to the committed reference manifests. SVGs scale without losing clarity.
