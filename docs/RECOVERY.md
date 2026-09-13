# Persistence, backup and recovery

Local named volumes are `openwebui_dex-data`, `openwebui_keycloak-db-data`, and the pre-existing external `open-webui`. Container restarts and Compose `down` preserve them; **do not run `down -v` when retaining data**. Secrets and import files under `.runtime` must be backed up along with databases. Re-generating secrets against existing state can break client and database authentication.

Run `scripts/backup-local.sh` to briefly stop SQLite writers and Keycloak, dump PostgreSQL, and copy Dex/Web UI data and bootstrap configuration into a private timestamped directory. The trap restarts services. Backups contain credentials and chat data; store encrypted with access controls and retention appropriate to your organization.

Restore into a **separate lab/project** first. Create new empty volumes, restore Dex and Web UI files preserving ownership/group permissions, restore PostgreSQL with `psql -U keycloak -d keycloak < keycloak.sql`, and restore matching client secrets/config. The target database must be empty for the plain dump. Reuse or deliberately rewrite issuer/callback URLs for the restore environment. Verify all five users, client secrets, broker links and representative chats. Only then plan a production cutover.

OpenShift backup equivalents: stop or quiesce Dex/Web UI before filesystem copies or consistent CSI snapshots; use logical database backups/PITR for PostgreSQL; include encrypted Secret backup and configuration Git revision. PVC snapshots alone are not a tested application recovery plan. Run your storage provider's restore procedure and verify SCC-compatible ownership on restored files.

Keycloak import does not update an existing realm. Restoring the database preserves federated users and active configuration; a realm export alone may omit operational data/session state. Never use `--import-realm` as a substitute for a PostgreSQL backup.

## Existing-email error after recreating demo Keycloak users

Deleting and recreating a Keycloak user changes its OIDC subject. Open WebUI retains the original subject and correctly refuses to silently link a new identity by email. Prefer restoring the original Keycloak database. For these five local fixtures only, `python3 scripts/repair-demo-links.py` verifies each stable Dex subject, restores missing fixture users, backs up WebUI SQLite in its persistent volume and explicitly reconciles the links without changing WebUI account IDs or chats. Run `python3 scripts/sync-keycloak.py` afterward, then verify both login modes. This repair is not a general enterprise account-linking policy; never enable blanket email merging as a workaround.
