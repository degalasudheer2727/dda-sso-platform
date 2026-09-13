ARG BASE_IMAGE=ghcr.io/dexidp/dex:v2.45.1@sha256:8499afd690c437f52301efd2b05b2455da5bd2dfc20332cd697dc9937f808462
FROM ${BASE_IMAGE}
# A presentation-only alias adapter: all verification remains in upstream Dex.
COPY dex/theme/password.html /srv/dex/web/templates/password.html
