# Enterprise production acceptance

This repository supplies a working local lab, an image-transfer kit, and a restricted-SCC-oriented OpenShift reference. It does not assert HA, zero downtime, regulatory compliance, certified platform compatibility, or completed disaster-recovery validation.

## Delivered controls

- Separate OIDC trust boundaries and confidential clients, authorization code + PKCE, exact redirect URI and signature/issuer validation.
- Direct upstream login with complete profiles; no second profile form or silent email-based account linking.
- Five synthetic identities with stable IDs, independently generated passwords, and non-admin Web UI roles.
- Persistent volumes and PostgreSQL, bootstrap Secret separation, pinned source versions/digests and offline runtime image archive.
- Native HTTPS Routes, startup/readiness/liveness probes, resource requests/limits, NetworkPolicy defaults, no privileged/anyuid requirement.
- Named administrator separation and first-user bootstrap protection in fresh OpenShift Web UI deployments.
- Repeatable configuration checks, actual browser SSO tests, invalid-redirect rejection, and local arbitrary-UID Web UI startup test.

## Release gates owned by the enterprise

| Gate | Required evidence before production |
|---|---|
| Platform support | Named OpenShift version, node architecture, image support owner, approved SCC/admission result |
| Identity governance | Real upstream connector, authoritative verified email/profile claims, MFA, access lifecycle and deprovisioning tests |
| Authorization | Approved user/admin mapping, denial tests for unauthorized identities, no first-user admin takeover |
| TLS/network | Trusted certificates in pods and browsers, renewal process, least-privilege ingress/egress with actual VIPs |
| Availability | SLO/RTO/RPO, HA database, supported multi-replica Dex/Web UI storage design, failure/load tests |
| Persistence | Storage class selected, capacity alerts, encrypted backups, a successful isolated restore drill |
| Supply chain | Final-image scanning/SBOM/signing, approved registry digests, registry credentials and update policy |
| Observability | Centralized sanitized logs, audit events, alert routing, retention/access controls |
| Data/privacy | Model-provider data policy, encryption at rest, retention, deletion, secret rotation evidence |
| Functional acceptance | Direct SSO, first login, repeat SSO, logout/expiry, user disablement, invalid redirect and chat/RAG tests |

## Availability boundary

The current Dex and Open WebUI SQLite stores intentionally have one replica and `Recreate`; adding replicas would be unsafe. PostgreSQL is a single instance. For enterprise HA use a supported PostgreSQL operator/service, migrate Dex to supported shared storage, and configure the Web UI version's supported external database/shared file storage/Redis architecture. Add disruption budgets and topology spread only after those services can safely run multiple replicas. A PDB on one SQLite replica is not HA.

## Audit and monitoring

Keycloak exposes internal readiness and (in the optimized image) metrics on port 9000. Route that port only to your approved monitoring stack, never publicly. Configure Keycloak login/admin events with retention and external audit collection per policy; avoid logging tokens/client secrets. Add alerts for pod restart loops, failed OIDC exchanges, repeated failed logins, database/PVC capacity, TLS expiry and backup age. A monitoring operator/ServiceMonitor is not assumed by the native base manifests.

## Administrator and secret lifecycle

Create named administrators with MFA, verify break-glass access, then retire temporary Keycloak bootstrap credentials. The generated Web UI bootstrap admin is separate from test identities. Keep rendered Secret files private or wrap them with your enterprise secret system. Rotate database credentials and both OIDC client secrets together with the dependent services; editing a Secret alone may not update database roles or imported Keycloak clients.

Only enable email trust for an upstream source whose email verification guarantees you have approved. A collision with an existing account fails for explicit administrator review. Test users and the static-password source are lab fixtures and must be removed/replaced for production.
