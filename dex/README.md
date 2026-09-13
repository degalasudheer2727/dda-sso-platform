# Dex — upstream OIDC provider

Image: `ghcr.io/dexidp/dex:v2.45.1`. [Official docs](https://dexidp.io/docs/) and [configuration example](https://github.com/dexidp/dex/blob/v2.45.1/examples/config-dev.yaml).

Local issuer: `http://dex.localhost:5556/dex`. Dex's client `keycloak-dda` allows only Keycloak's `/realms/dda/broker/dex/endpoint` callback. The generated config uses bcrypt password hashes for five synthetic identities; plaintext passwords appear only in `.runtime/TEST-USERS.md` and private bootstrap state. The gRPC management port is not exposed.

The storage volume `/var/dex` contains a SQLite database with signing keys and sessions. Preserve it across restarts. One replica with a `Recreate` strategy is intentional; SQLite must not be shared between replicas. For HA replace SQLite with supported PostgreSQL storage and validate migration before scaling.

Configuration logic is `dex_config()` in `scripts/bootstrap.py`; `.runtime/dex/config.yaml` is the local rendered form. OpenShift receives this configuration as a Secret, not a public ConfigMap. Reference manifests: `openshift/reference/dex/`.

User onboarding is declarative for this demo. Edit the generator/input, regenerate and restart Dex to change static users, preserving the stable `userID`. Changing an ID creates a different identity. For enterprise use replace demo passwords with your LDAP/AD or external OIDC connector, configure that connector's network policy/CA, and remove static test users. `render-openshift.py` includes no demo users unless explicitly passed `--with-demo-users`.

Checks: discovery `.../dex/.well-known/openid-configuration`; management health `/healthz` on internal port 5558. The browser cannot use an internal-only issuer URL; all parties must agree on the public issuer.
