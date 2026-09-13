# Dex — upstream OIDC provider

Image: `dda/dex:v2.45.1`, built from digest-pinned upstream Dex with `dex/Dockerfile`. [Official docs](https://dexidp.io/docs/) and [configuration example](https://github.com/dexidp/dex/blob/v2.45.1/examples/config-dev.yaml).

Local issuer: `http://dex.localhost:5556/dex`. Dex's client `keycloak-dda` allows only Keycloak's `/realms/dda/broker/dex/endpoint` callback. The generated config uses bcrypt password hashes for five synthetic identities; plaintext passwords appear only in `.runtime/TEST-USERS.md` and private bootstrap state. The gRPC management port is not exposed.

The storage volume `/var/dex` contains a SQLite database with signing keys and sessions. Preserve it across restarts. One replica with a `Recreate` strategy is intentional; SQLite must not be shared between replicas. For HA replace SQLite with supported PostgreSQL storage and validate migration before scaling.

Configuration logic is `dex_config()` in `scripts/bootstrap.py`; `.runtime/dex/config.yaml` is the local rendered form. OpenShift receives this configuration as a Secret, not a public ConfigMap. Reference manifests: `openshift/reference/dex/`.

User onboarding is declarative for this demo. Edit the generator/input, regenerate and restart Dex to change static users, preserving the stable `userID`. Changing an ID creates a different identity. For enterprise use replace demo passwords with your LDAP/AD or external OIDC connector, configure that connector's network policy/CA, and remove static test users. `render-openshift.py` includes no demo users unless explicitly passed `--with-demo-users`.

Checks: discovery `.../dex/.well-known/openid-configuration`; management health `/healthz` on internal port 5558. The browser cannot use an internal-only issuer URL; all parties must agree on the public issuer.

## Username or email login

The browser login accepts `testuser01` through `testuser05`, or `admin`, as well as their existing email addresses, using the same passwords. The template maps these six demo aliases to canonical emails immediately before form submission; upstream Dex still validates the password. Existing user IDs, display names, roles and federated accounts remain unchanged. Aliases are case-insensitive; unknown inputs are passed to Dex for normal validation.

This is a browser form adapter for the fixed demo identities, not native username authentication in Dex's local password API. JavaScript is required for aliases; email login works without it. If you change fixture usernames or emails, update `theme/password.html` and rebuild the image. For enterprise LDAP/AD, use the connector's native username attribute and remove this demo adapter. The OpenShift manifests and air-gap export use the same derived image.

Template adapted from [Dex v2.45.1 password.html](https://github.com/dexidp/dex/blob/v2.45.1/web/templates/password.html), under Dex's Apache-2.0 license.

Verify both modes: `python3 scripts/onboard-test-users.py --username`, then the same command without `--username`. Add `--admin` to verify the administrator.
