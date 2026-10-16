FROM ghcr.io/astral-sh/uv:0.13.1@sha256:4a1f3666816dafadd20ceb71eac9a7d56d7ef30279f7d64048519ab901ada336 AS uv
FROM python:3.12-slim-trixie@sha256:a6e34c598f2467ed0e9a8d349809fcd8b5c603269512df273a0bb1784edc11b1 AS build
COPY --from=uv /uv /usr/local/bin/uv
ENV UV_PYTHON_DOWNLOADS=never UV_LINK_MODE=copy UV_PROJECT_ENVIRONMENT=/opt/venv
WORKDIR /build
COPY pyproject.toml uv.lock ./
COPY app ./app
COPY migrations ./migrations
RUN uv sync --locked --no-dev --no-editable

FROM build AS test
RUN uv sync --locked --no-editable
COPY tests ./tests
COPY docker ./docker
ENV PYTHONDONTWRITEBYTECODE=1
USER 10001:10001
CMD ["/opt/venv/bin/python", "-m", "pytest", "-q", "-m", "not integration", "-p", "no:cacheprovider"]

FROM python:3.12-slim-trixie@sha256:a6e34c598f2467ed0e9a8d349809fcd8b5c603269512df273a0bb1784edc11b1 AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PATH=/opt/venv/bin:$PATH
RUN groupadd --gid 10001 county && useradd --uid 10001 --gid county --no-create-home county
COPY --from=build /opt/venv /opt/venv
COPY docker/entrypoint.py /opt/container/entrypoint.py
USER 10001:10001
WORKDIR /opt/container
ENTRYPOINT ["python", "/opt/container/entrypoint.py"]
CMD ["serve"]
