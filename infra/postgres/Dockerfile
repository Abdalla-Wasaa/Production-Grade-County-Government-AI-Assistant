FROM postgres:17-bookworm@sha256:3645570cccdfa447589da9f57dd740faa29b30938e861289a5574b6ca6b03826
# Compose always starts as UID 999. Remove the unused root-to-postgres helper,
# which embeds an outdated Go runtime; this image intentionally cannot demote root.
RUN rm /usr/local/bin/gosu
USER 999:999
