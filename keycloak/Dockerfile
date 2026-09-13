ARG BASE_IMAGE=quay.io/keycloak/keycloak:26.7.3
FROM ${BASE_IMAGE} AS builder
ENV KC_DB=postgres KC_HEALTH_ENABLED=true KC_METRICS_ENABLED=true
RUN /opt/keycloak/bin/kc.sh build
FROM ${BASE_IMAGE}
COPY --from=builder /opt/keycloak/ /opt/keycloak/
ENV KC_DB=postgres KC_HEALTH_ENABLED=true KC_METRICS_ENABLED=true
ENTRYPOINT ["/opt/keycloak/bin/kc.sh"]
