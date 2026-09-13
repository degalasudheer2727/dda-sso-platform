# Administration accounts

Private local credentials are in `.runtime/ADMIN-ACCESS.md`; do not commit, screenshot or publish that file. Each administrator credential is generated independently. The five regular personas remain non-admin.

| System | Default local administrator | Administration method |
|---|---|---|
| Dex identities | `admin@dda.test` | Fully populated upstream SSO identity. Dex configuration itself is managed through versioned configuration; Dex has no user-admin web console. |
| Keycloak server | `admin` in `master` | `/admin/` with the generated master-admin password. |
| Keycloak `dda` realm | `admin@dda.test` through Dex | `/admin/dda/console/`; only this identity receives `realm-management/realm-admin`. |
| Open WebUI | `admin@dda.test` through Dex | App user menu → Admin Panel. Keycloak's `webui-admin` claim grants administrator access. Existing app administrators are preserved. |
| PostgreSQL | `postgres` | Internal `psql`/approved DBA tools, with generated superuser password; no public database port. Application uses the separate `keycloak` role. |
| Headroom | No built-in user administration | Local loopback dashboard and Docker configuration. No fictitious admin account is added to a service without authentication support. |

The ordinary identities receive Keycloak `webui-user`. The dedicated SSO administrator receives `webui-admin` and realm administration. Dex cannot grant downstream administrator rights merely by changing an email string; administrator role assignment is explicit in Keycloak. In enterprise environments, restrict who can assign these roles and audit every change.

Fresh OpenShift Web UI deployments seed a separate bootstrap administrator before allowing SSO, preventing the first test user from becoming admin. The production renderer also provisions the Keycloak master bootstrap administrator and PostgreSQL superuser credential. A real upstream enterprise administrator must be explicitly linked/assigned the appropriate Keycloak role; importing demo users is opt-in. The temporary bootstrap accounts must be replaced by named MFA-protected administrators after acceptance.

The rendered demo realm pre-provisions the administrator using the stable local-connector subject verified against the pinned Dex version; no password is stored in Keycloak for that federated user. For the demo fixture, run `scripts/sync-keycloak.py` after the administrator's first SSO login to assign its explicit roles, then sign in again so a new token includes them. Restart import files do not update existing realms.
