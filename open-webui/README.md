# Open WebUI — Keycloak relying party

Version v0.11.3. Local URL: `http://webui.localhost:3000`. The app trusts only Keycloak's `dda` discovery document. The dedicated client uses a generated secret, authorization code + PKCE, `openid email profile`, and an exact callback.

OAuth registration is enabled and email merging disabled. Local password sign-in remains visible to preserve the existing administrator. The existing database's persisted user-role policy takes precedence over the environment default; `scripts/approve-test-users.py` approves only the five generated accounts after their brokered login. Other existing users are untouched.

OpenShift starts with a fresh PVC, defaults SSO users to role `user`, disables the password login form, and seeds a separate bootstrap admin from a generated Secret before the first SSO login. To use that admin for emergency recovery, temporarily enable the login form through a controlled deployment change, then disable it afterward. OIDC role mapping is explicit: `webui-user` grants ordinary access and only `webui-admin` grants administration. The dedicated demo administrator is assigned that role in Keycloak. Audit real enterprise role assignments; ordinary upstream users must not become admins.

The Dockerfile derives a runtime that permits OpenShift arbitrary UIDs to write the needed application paths while retaining `runAsNonRoot`. It has been smoke-tested with UID `1000710000` and GID `0`. Fresh PVC ownership is assigned by the restricted SCC/fsGroup policy; restored volumes still need matching group permissions.

Air-gap mode disables model downloads and version checks. Local embedding files present in the base image can be used, but speech/RAG models and model-provider services are separate dependencies. Mirror and license-check any additional model artifacts, configure your internal inference URL, CA trust and egress policy, and test chat/RAG independently. SSO success alone does not validate an LLM connection.

Data lives at `/app/backend/data` on a 10 Gi PVC. SQLite requires one replica and `Recreate`; scaling needs a supported external database and shared storage design. Reference files: `openshift/reference/open-webui/`.

Local identity Compose also enables `OFFLINE_MODE`, `HF_HUB_OFFLINE`, and disables version checks, matching the air-gap image behavior. This avoids external model downloads during startup; document embeddings require a model already present in the cache or an approved internal embedding service. An init process handles child processes during local container shutdown.
