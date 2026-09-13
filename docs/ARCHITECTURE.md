# Trust and identity flow

1. Browser opens Open WebUI and chooses DDA SSO.
2. Web UI creates an OAuth state/nonce and PKCE challenge, redirects to Keycloak's `dda` authorization endpoint.
3. The `kc_idp_hint=dex` parameter makes Keycloak immediately redirect to Dex; its broker authenticates with Dex using the confidential `keycloak-dda` client.
4. Dex validates a test identity's bcrypt password, returns an authorization code, and supplies signed identity claims to Keycloak.
5. Keycloak verifies the issuer/signature, applies the unique-user provisioning flow without asking for profile details, and creates a linked user in PostgreSQL.
6. Keycloak returns a code to Web UI's exact callback. Web UI exchanges it with its own client secret and PKCE verifier, validates the Keycloak identity token and creates its application user/session.

There are two separate client secrets and two distinct trust boundaries. Web UI trusts Keycloak, not Dex directly. User passwords exist only at Dex; Keycloak stores a federated link. The client's direct password grants are disabled. Existing accounts are not silently merged by matching email.

## Local versus OpenShift

| Concern | Mac lab | OpenShift reference |
|---|---|---|
| URL | `.localhost` and loopback published ports | routable HTTPS DNS and Routes |
| Keycloak | `start-dev` | prebuilt optimized production `start` |
| Persistence | named Docker volumes | RWO PVCs + PostgreSQL |
| Secrets | ignored `.runtime` files | generated Secrets / enterprise secret manager |
| Runtime identity | upstream default container users | SCC-assigned arbitrary UID, no privilege escalation |
| Certificates | HTTP lab only | trusted Route CA, verified back-channel TLS |
| User source | five synthetic Dex passwords | enterprise connector, test identities opt-in |
| Model downloads | existing local setup | offline mode, approved mirrored models |
| Replicas | one each | one each until HA storage design is supplied |

Dex's SQLite storage is intentionally selected for a lightweight reproducible upstream provider. The five users are a test fixture, not an enterprise credential directory. The Keycloak brokerage makes replacing Dex with a real corporate OIDC/LDAP source possible without changing Web UI's trusted issuer/client.
