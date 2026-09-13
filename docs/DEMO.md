# Complete demo walkthrough

Keep Docker Desktop running. Start/check the stack with `scripts/local.sh up -d` and `scripts/local.sh ps`. Use the private `.runtime/TEST-USERS.md` and `.runtime/ADMIN-ACCESS.md` for credentials.

## Ordinary user experience

1. Open `http://webui.localhost:3000/auth` in a fresh browser session.
2. Click **Continue with DDA SSO**. You should land directly on the **Dex** email/password form; no Keycloak provider-selection page appears.
3. Sign in with `testuser01@dda.test` (Alex Morgan) and its generated password.
4. The browser returns to Open WebUI without a second profile form. The full name comes from Dex through Keycloak. The account has ordinary user access.
5. Open `http://keycloak.localhost:8080/realms/dda/account/` in the same browser. The existing Keycloak session provides SSO.
6. Repeat in isolated browser sessions for Jamie Parker, Taylor Reed, Jordan Blake and Casey Brooks. No ordinary user should have an Admin Panel.

## Administrator experience

1. In a separate browser session, open Web UI and sign in through Dex as `admin@dda.test`.
2. Open the user menu → **Admin Panel**. The administrator can inspect the five ordinary users.
3. Open `http://keycloak.localhost:8080/admin/dda/console/` in that same session. Inspect the `dda` realm, `dex` identity provider, `open-webui` client, and brokered users/roles.
4. Use `http://keycloak.localhost:8080/admin/` and master username `admin` only for server-wide administration.
5. Dex configuration and PostgreSQL are administered through their configuration/DB tools; they are not presented as additional SSO web consoles.

## Operational demo

- `python3 scripts/verify-local.py`: checks five ordinary roles, federation links, complete profiles, PKCE and invalid-redirect rejection.
- `make validate`: validates reproducible native resource relationships and security settings.
- `scripts/backup-local.sh`: quiesced local backup (brief outage).
- Restart the identity containers and rerun verification to demonstrate persistence.
- Inspect `openshift/reference/` and `docs/AIRGAP.md`, then the image archive under `.runtime/airgap/`.

A successful login demonstrates identity integration. Select/configure a model provider separately to demonstrate AI chat. Closing a browser is not equivalent to revoking all server-side sessions; demonstrate your required logout and expiry behavior separately.
