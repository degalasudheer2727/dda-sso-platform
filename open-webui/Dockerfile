ARG BASE_IMAGE=ghcr.io/open-webui/open-webui:v0.11.3
FROM ${BASE_IMAGE}
USER 0
# OpenShift assigns an arbitrary UID in the root group. Writable app paths only.
RUN mkdir -p /app/backend/data /app/backend/open_webui/static /app/backend/static && \
    chgrp -R 0 /app/backend/data /app/backend/open_webui/static /app/backend/static && \
    chmod -R g=u /app/backend/data /app/backend/open_webui/static /app/backend/static
ENV HOME=/tmp OFFLINE_MODE=true HF_HUB_OFFLINE=1 ENABLE_VERSION_UPDATE_CHECK=false
USER 1001
