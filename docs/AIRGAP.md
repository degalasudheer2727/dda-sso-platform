# Air-gapped enterprise handoff

## 1. Decide environment parameters

Record OpenShift version/architecture, internal registry/repository, namespace, storage class, application DNS domain, ingress CA/certificate, approved image provenance/scanning policy, internal time/DNS services, and inference endpoint. OIDC requires synchronized clocks, browser trust, exact public issuers and working pod→Route connectivity. The current bundle is **linux/amd64** from this Intel Mac. Rebuild/export for the actual cluster architecture; do not assume an AMD64 Docker archive is a multi-architecture image.

## 2. Build and mirror while connected

```sh
docker pull ghcr.io/dexidp/dex:v2.45.1
docker pull quay.io/keycloak/keycloak:26.7.3
docker pull quay.io/sclorg/postgresql-16-c9s@sha256:fbef891ec464ee8d20332c7f9a4a68decc0b6db8460e7e875df6f33cac5003dc
docker pull ghcr.io/open-webui/open-webui:v0.11.3
docker build -t dda/keycloak:26.7.3 -f keycloak/Dockerfile .
docker build -t dda/open-webui:v0.11.3 -f open-webui/Dockerfile .
scripts/export-images.sh
```

Transfer `.runtime/airgap/dda-images.tar`, its checksum, this Git repository, approved scanner/signature/SBOM reports, required client binaries (`oc`, Python 3, Podman), and the enterprise CA through your sanctioned process. Verify the checksum **before loading**. The generated archive contains image layers only, not local databases, test passwords or Codex credentials. `.dockerignore` excludes workspace files from image build contexts.

Versions are pinned; source digests and local image IDs are recorded in `images.lock.json`. In a regulated pipeline, scan/sign the final derived images and record **destination registry digests after push**. Substitute those immutable destination digests in the generated deployments. Local Docker image IDs are not registry manifest digests, and multi-architecture source digests may differ from platform/destination digests. Do not treat this demo as evidence that an image passed your vulnerability policy.

## 3. Import inside the disconnected network

```sh
# Verify the copied archive against its checksum using the same file name/path.
sha256sum dda-images.tar
podman login registry.enterprise.example
scripts/import-images.sh registry.enterprise.example/dda /transfer/dda-images.tar
```

Use TLS verification and install the registry CA in the transfer host/container runtime trust stores. Configure the OpenShift namespace's image pull secret. The custom image builds have already happened outside the air gap, so cluster startup needs no package repositories, Maven, npm or pip downloads.

## 4. Generate private cluster configuration

Run `scripts/render-openshift.py` with actual `--domain`, `--registry`, `--namespace`, `--storage-class`, and `--ca-bundle`; see `openshift/README.md`. Omit `--with-demo-users` for production and configure Dex's enterprise connector. For an isolated test replica, explicitly include the five demo users. Avoid transferring local runtime secrets to production: each new output directory generates independent database/client/admin secrets.

The Route wildcard certificate must cover `dex.<domain>`, `keycloak.<domain>`, `webui.<domain>`. Distribute trusted roots to browsers too. Route edge TLS means traffic from router to pod is HTTP; use re-encrypt Routes and pod TLS if your security baseline requires in-cluster encryption.

## 5. Admit, deploy and prove the complete flow

Render and validate with `oc kustomize`; run server-side dry-run and admission review on the intended cluster. Apply namespace/pull-secret prerequisites, then the manifests. Check PVC binding, SCC-assigned UID/fsGroup, image pulls, health probes, NetworkPolicies and routes. From the Keycloak pod resolve/reach Dex's public issuer; from Web UI reach Keycloak's public issuer with TLS verification enabled. Do not replace public issuer URLs with cluster service names to work around DNS.

Log in through Web UI for all authorized test personas; verify the final issuer is Keycloak `/realms/dda`, account roles are correct and no test user is admin. Test a second app/account console for SSO, reauthentication after session expiry, logout behavior, negative logins, invalid redirect URIs, app restarts and restored databases. Dex local-password sessions are not a full enterprise global-logout implementation: ending Keycloak/Web UI sessions does not revoke every upstream provider session or issued JWT immediately. Validate required logout semantics with the actual enterprise IdP.

Configure a licensed internal model provider and test chat/RAG separately. The included Open WebUI runtime has offline mode on; any additional embedding/Whisper models need a mirrored artifact and an explicit startup test with network access disabled. No live OpenShift or enterprise inference validation was performed in this Mac-only deployment.

## 6. Operationalize

Replace temporary administrators with named MFA-protected admins. Rotate client/database secrets through coordinated application updates. Establish database/PVC backups, successful restore drills, log/audit retention, vulnerability patch cadence and certificate renewal. Keep one replica for the SQLite-backed demo services. For availability requirements, design supported PostgreSQL HA, Dex storage migration and scalable Web UI storage before adding replicas.
