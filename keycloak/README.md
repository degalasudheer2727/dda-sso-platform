# Keycloak — DDA broker and SSO issuer

Version 26.7.3. [Container guide](https://www.keycloak.org/server/containers), [hostname guide](https://www.keycloak.org/server/hostname), [identity brokering](https://www.keycloak.org/docs/latest/server_admin/#_identity_broker).

Realm: `dda`. Identity provider alias: `dex`. Client: `open-webui`, confidential, authorization-code flow, PKCE S256, exact callback `/oauth/oidc/callback`. Password/direct-access grants and service accounts are disabled for that client. The broker validates Dex signatures using its JWKS endpoint. `trustEmail=true` applies only to this controlled demo upstream; revisit email verification guarantees when changing providers. Email-based auto-linking in Open WebUI is disabled.

The first login creates a federated Keycloak user. The dedicated `dda-first-broker-login` flow provisions a unique identity without a second profile form and rejects collisions instead of silently linking existing accounts. Full names and dummy emails are supplied by Dex and refreshed with `syncMode=FORCE`. Open WebUI sends `kc_idp_hint=dex` to skip the broker-selection screen. Five browser logins exercise this path. The Keycloak account console can demonstrate SSO after logging into Web UI.

`realm()` in `scripts/bootstrap.py` defines the realm. Local output: `.runtime/keycloak/dda-realm.json`. Reference configuration: `realm-template.json`; native resources: `openshift/reference/keycloak/`.

Local Docker uses `start-dev` with HTTP on loopback for ease of preview. OpenShift uses the optimized `Dockerfile`, `start --optimized --import-realm`, a full HTTPS hostname, and `KC_PROXY_HEADERS=xforwarded` behind a TLS-terminating Route. Backend HTTP is limited by NetworkPolicy to ingress traffic. If policy mandates encryption all the way to the pod, switch to re-encrypt Routes with pod certificates and the appropriate HTTPS configuration; edge termination alone does not supply that.

Realm import is **first boot only** and skips an existing realm. Editing an import file does not reconcile a live database. Use the Admin REST API/console for controlled subsequent changes and update the source template to match. Do not delete production databases to reimport. Back up PostgreSQL before updates; upgrade versions deliberately. The bootstrap administrator is temporary: provision named administrators with MFA and remove the bootstrap user after validation.

Persistent identity/broker state lives in PostgreSQL. `/opt/keycloak/data` is disposable in OpenShift. Health endpoint: `:9000/health/ready`; it is not exposed in the public Route.
