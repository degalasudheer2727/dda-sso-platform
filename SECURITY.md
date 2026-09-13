# Credential handling and deployment security

No production credentials are shipped. Bootstrap generates independent random passwords/client secrets and stores them under private, ignored `.runtime/` files. Rendered cluster Secrets, database backups, image archives and browser-private state are also ignored. Only placeholder Secrets are committed. Authenticated screenshots/video remain local and are excluded from publication; architecture source diagrams contain no authentication state. `scripts/check-secrets.py` scans the Git index for private paths, known local generated credentials and common credential patterns; it runs in CI as well (known-local checks apply only when that local state exists).

Keep GitHub visibility private unless the repository has been deliberately reviewed for publication. Never add `.runtime/`, backups, deployment-secrets.json or real rendered Secret manifests to Git. Use your enterprise secret management/encryption workflow for GitOps. A private repository is not a substitute for keeping secrets out of version control.

The local demo binds public service ports to loopback and uses HTTP only for the Mac experience. Enterprise deployments require verified HTTPS, approved network policies and the production gates in `docs/PRODUCTION-READINESS.md`. Do not forward these local ports to public networks.

Administrator credentials are separate per service. The five personas are non-admin. Role elevation is explicit in Keycloak; upstream email alone does not grant administration. Dex/Headroom do not have web-admin account models and are administered through configuration/runtime access. Treat Docker daemon access as administrative host access.

If a credential is exposed, rotate it in the authoritative service and dependent clients immediately, then remove it from Git history using your organization's incident process. Do not merely delete it in a later commit. Coordinate database/client credential rotation with persisted service state; replacing an import file or Secret alone may not update the initialized database.
