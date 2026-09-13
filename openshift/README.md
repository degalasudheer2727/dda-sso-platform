# Native OpenShift resources

`reference/` contains committed, inspectable Deployments, Services, Routes, PVCs, Secrets with placeholders, and NetworkPolicies. Files use JSON syntax, which is valid YAML and supported by `oc`/Kustomize. `rendered/` is private output and is ignored by Git.

```sh
python3 scripts/render-openshift.py \
  --domain apps.enterprise.example \
  --registry registry.enterprise.example/dda \
  --namespace dda-sso \
  --storage-class enterprise-rwo \
  --ca-bundle /path/to/enterprise-ca-chain.pem
python3 scripts/verify-manifests.py openshift/rendered
oc kustomize openshift/rendered > /secure/path/dda.yaml
oc apply --dry-run=server -f /secure/path/dda.yaml
oc apply -f /secure/path/dda.yaml
oc -n dda-sso rollout status deploy/dex
oc -n dda-sso rollout status deploy/keycloak-db
oc -n dda-sso rollout status deploy/keycloak
oc -n dda-sso rollout status deploy/open-webui
```

Create the namespace first if server-side dry-run requires it, and configure its private registry pull secret/service account before application deployment. Without `--with-demo-users`, Dex has no local test identities: configure the intended enterprise connector before expecting logins. For a nonproduction replica, explicitly add that flag after `scripts/bootstrap.py` has generated demo identities.

DNS names are `dex.<domain>`, `keycloak.<domain>`, `webui.<domain>`. Use a trusted ingress certificate or provide its full CA chain. `--ca-bundle` configures Keycloak trust and Python/Open WebUI certificate verification; it never turns off TLS verification. The Python bundle replaces its default CA bundle, so include all enterprise roots needed by your model and identity services.

NetworkPolicy defaults to deny. DNS to OpenShift DNS, ingress-router traffic, and Keycloak→PostgreSQL are allowed. Keycloak and Web UI can reach TCP 443 for public Route hairpin traffic; narrow this rule to the real ingress VIP/CIDR for your network. Add explicit egress for an internal LLM service if it uses another port. Host-network ingress and DNS policy behavior depends on the cluster network plugin: test and adjust selectors/CIDRs in the target cluster.

No fixed UID, privileged container, hostPath, or anyuid SCC is requested. The cluster supplies allowed UID/fsGroup values. Route, SCC admission, CA chain, registry authentication, storage provisioning, and NetworkPolicy behavior still require validation on the actual enterprise cluster. These manifests do not claim compatibility certification for an unspecified OpenShift version.

Generated secrets persist across rerenders in `rendered/deployment-secrets.json`. Use a separate output directory per environment. Back it up securely; credential rotation requires matching database/client updates. For GitOps, replace plaintext rendered Secrets with your approved sealed/encrypted secret process.
