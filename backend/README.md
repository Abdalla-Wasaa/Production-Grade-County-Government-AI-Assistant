# FastAPI backend foundation

P1-01 implements process liveness and HTTP/configuration boundaries for a fictional
county environment. Use synthetic data only. No authentication, database/models,
chat, provider calls, agents, RAG, tools, containers or deployment are implemented.
`GET /health/ready` remains absent until P1-02; a 200 liveness response does not
establish infrastructure readiness or production approval.

## Setup

Use Python 3.12 and uv 0.13.1. Install uv separately using its
[official instructions](https://docs.astral.sh/uv/getting-started/installation/)
and select the pinned version. Work in this project's backend directory, never in
the coursework environment. From the repository root:

```bash
cd backend
uv --version
uv sync --locked --python 3.12
uv pip check --python .venv/bin/python
COUNTY_ENVIRONMENT=development uv run --locked uvicorn app.main:create_app --factory --host 127.0.0.1 --port 8000 --no-access-log
```

From a second terminal:

```bash
curl --fail http://127.0.0.1:8000/health/live
```

The body is `{"status":"ok"}`. Each response has a server-generated `X-Request-ID`
and `Cache-Control: no-store`. Stop the local server with Ctrl+C. Uvicorn access
logging is explicitly disabled because request URLs can contain personal data or
credentials. Application logs are separate JSON operational events; Uvicorn startup
messages are server logs, not this application's structured event stream.

Alternatively, copy the example to a project-local ignored `.env` and opt in:

```bash
cp .env.example .env
uv run --locked --env-file .env uvicorn app.main:create_app --factory --host 127.0.0.1 --port 8000 --no-access-log
```

The app never discovers a parent/current-directory `.env` implicitly. No API key,
JWT secret or database URL is required for P1-01. Do not add credentials just to
make health tests pass. `.env` is local-only and must never be committed.

## Configuration contract

| Variable | Required / default | Validation |
| --- | --- | --- |
| `COUNTY_ENVIRONMENT` | Required | Only `development` or `test`; deployment modes are deliberately unavailable |
| `COUNTY_LOG_LEVEL` | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `COUNTY_CORS_ORIGINS` | JSON array; empty by default | Explicit unique loopback HTTP(S) origins only; no wildcard, credentials, paths, query or fragments |

No CORS origin is allowed by default. For local frontend development, explicitly
allow localhost/127.0.0.1 port 5173 (as in the example). Allowed methods currently
contain only GET; credentialed CORS is disabled because cookie authentication is
not implemented. CORS is a browser read policy, not authentication/network isolation:
requests from a disallowed origin can still reach the public liveness endpoint,
but do not receive an allow-origin header. Preflight failures use a safe JSON error.
Future authentication/CORS changes require the Phase 2 contract and tests.

Missing/malformed settings raise a safe `ConfigurationError` at factory invocation.
Raw validation input/cause text is suppressed. Programmatic tests can inject a
validated `Settings` instance into `create_app(settings)` without process-global
settings caches. Importing `app.main` constructs no app, logger handlers, or clients.

## Package boundaries and HTTP behavior

- `app/main.py`: factory, lifespan and explicit composition.
- `app/core/config.py`: validated local-only Pydantic Settings.
- `app/core/logging.py`: JSON formatter allowing fixed events and bounded typed fields.
- `app/core/middleware.py`: request IDs, sanitized unexpected errors, CORS normalization.
- `app/core/errors.py`: typed, localized error envelopes and framework handlers.
- `app/api/health.py`: typed, dependency-free liveness response.
- `app/api/v1/`: reserved router prefix; no fake business endpoint is added.
- `tests/`: configuration, lifecycle, HTTP, CORS, logging and import regressions.

OpenAPI is available locally at `/api/v1/openapi.json`; interactive Swagger/ReDoc
pages are disabled to avoid externally hosted UI assets. Operational health paths
remain outside `/api/v1`. The only application endpoint is `GET /health/live`.

404, 405, request-validation failures, rejected preflights and unexpected 500s share
`error.code`, `message`, `request_id`, `details`. `Accept-Language: sw` selects fixed
Kiswahili error messages; other values default to English. Full language negotiation
and review of public product copy are later work. Validation details identify the
request generically rather than echoing user-controlled JSON keys/values. Unexpected
errors do not return/log stack traces. No exception-driven response replacement is
attempted after headers have already been sent; streaming is outside this milestone.

Lifespan installs/removes an application-owned stream handler, emits startup/shutdown
events and tracks local lifecycle state. No placeholder pools/AI clients are created.
Logging is redacted by omission: unknown messages/extras, bodies, headers, paths,
configuration, exception text and traceback are dropped. Allowed output is timestamp,
level, fixed event and validated request ID/method/status/duration. Adding new log
fields requires review and privacy regression tests. This policy applies to the
application logger, not arbitrary third-party/server loggers or OS-level capture.

## Checks

```bash
uv lock --check
uv sync --locked
uv pip check --python .venv/bin/python
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked pytest -q
git -C .. diff --exit-code -- backend/uv.lock
```

Tests block network connections and require no database, cloud or model credentials.
Test-only routes exercise 422/500 handling without adding product endpoints. Existing
repository documentation/security checks still apply. The Backend workflow runs the
same locked Python 3.12 checks on pushes and PRs; it does not start P1-02 services.

## Dependency decision and limits

Python/Requires-Python metadata and direct dependency constraints were checked before
resolution on 2026-10-16. The lock resolves FastAPI 0.143.2, Pydantic 2.14.1,
pydantic-settings 2.16.0, Starlette 0.52.1, Uvicorn 0.54.0, HTTPX 0.28.1,
Pytest 9.1.1 and Ruff 0.14.0. Runtime/dev dependencies are isolated in `backend/.venv`;
repository tooling retains `requirements-dev.txt`. `uv.lock` records transitive
versions and distribution hashes from public PyPI. Exact compatibility is verified
through locked sync, dependency checking and tests; metadata alone is insufficient.

Starlette is a direct dependency because its middleware/types are used. It is bounded
below 1.0 for this HTTPX-based test harness; the newest 1.x release signals a switch
to HTTPX2. The tested 0.52.1 combination emits an upstream AnyIO BlockingPortal
deprecation warning. It is recorded rather than hidden; revisit the pair in a focused
dependency update. This foundation is not an authentication, privacy-compliance,
dependency-vulnerability or production-readiness certification.

Review [approved scope](../docs/REQUIREMENTS.md), [architecture](../docs/ARCHITECTURE.md)
and the [pre-pilot gate](../docs/PRE_PILOT_GATE.md) before expanding functionality.
