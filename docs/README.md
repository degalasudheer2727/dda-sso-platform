# DDA documentation

Start with the [illustrated configuration guide](CONFIGURATION-GUIDE.md) or its [offline HTML preview](CONFIGURATION-GUIDE.html).

| Document | Purpose |
|---|---|
| [Configuration guide](CONFIGURATION-GUIDE.md) | Screenshots and operating instructions for the deployed SSO solution |
| [Runtime reference](configuration/local-effective-config.json) | Allowlisted live configuration without credentials |
| [Administration](ADMINISTRATION.md) | Administrator entry points and account boundaries |
| [Demo](DEMO.md) | User SSO and group-permission demonstration |
| [Air gap](AIRGAP.md) | Image mirroring, CA and OpenShift rollout |
| [Recovery](RECOVERY.md) | Backup, restore and identity-link recovery |
| [Production readiness](PRODUCTION-READINESS.md) | Remaining enterprise acceptance requirements |
| [Architecture](ARCHITECTURE.md) | Architecture notes and editable diagrams |

To refresh the public configuration reference, run `python3 scripts/export-config-reference.py` against the local lab. Review the output before committing. Rebuild the offline guide with `python3 scripts/render-configuration-guide.py`. Keep the screenshots directory next to the HTML when transferring it offline.
