# PostgreSQL for Keycloak

Uses the SCLorg PostgreSQL 16 CentOS Stream 9 image, pinned by digest locally. [Maintainer documentation](https://github.com/sclorg/postgresql-container). This container supports arbitrary OpenShift user IDs and uses `POSTGRESQL_USER`, `POSTGRESQL_PASSWORD`, and `POSTGRESQL_DATABASE`.

Database/user: `keycloak`. Data: `/var/lib/pgsql/data`, a persistent named volume locally and a 10 Gi RWO PVC on OpenShift. Port 5432 has no host binding or Route. NetworkPolicy permits only Keycloak. The reference requests one replica; it is not a database cluster.

Password changes in Kubernetes Secrets do not by themselves rotate an initialized database role. Coordinate `ALTER ROLE`, Secret updates, and Keycloak restart. Back up with `pg_dump -U keycloak keycloak`; verify restoration into a separate database. For enterprise HA/PITR use your supported database operator/service and adjust Keycloak's JDBC configuration.

Native files are in `openshift/reference/keycloak-db/`. Storage class and enterprise backup/retention policy must be chosen before production deployment.
