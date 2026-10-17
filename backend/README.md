# FastAPI backend foundation

P1-02 adds PostgreSQL 17 connectivity, explicit Alembic migrations and database
readiness to the existing process/configuration/HTTP foundation. Use fictional
county information only. No domain tables, auth, chat or AI are implemented. The repository now includes
the P1-03 independent frontend shell and P1-04 local Compose stack; these do not
add a frontend API consumer or authorize deployment. Liveness does not establish production readiness.

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
JWT secret or database URL is required to start the process. Do not add credentials just to
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
remain outside `/api/v1`. Operational endpoints are `GET /health/live` and `GET /health/ready`.

404, 405, request-validation failures, rejected preflights and unexpected 500s share
`error.code`, `message`, `request_id`, `details`. `Accept-Language: sw` selects fixed
Kiswahili error messages; other values default to English. Full language negotiation
and review of public product copy are later work. Validation details identify the
request generically rather than echoing user-controlled JSON keys/values. Unexpected
errors do not return/log stack traces. No exception-driven response replacement is
attempted after headers have already been sent; streaming is outside this milestone.

Lifespan installs/removes an application-owned stream handler, emits startup/shutdown
events and tracks local lifecycle state. A configured database receives a lazy lifespan-owned pool, disposed on shutdown.
No AI clients are created.
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
uv run --locked mypy
uv run --locked pytest -q -m "not integration"
git -C .. diff --exit-code -- backend/uv.lock
```

Unit tests block network connections and require no database, cloud or model credentials.
Test-only routes exercise 422/500 handling without adding product endpoints. Existing
repository documentation/security checks still apply. The Backend workflow runs the
same locked Python 3.12 checks plus a separate PostgreSQL 17 integration job.

## Dependency decision and limits

Python/Requires-Python metadata and direct dependency constraints were checked before
resolution on 2026-10-16. The historical P1-01 lock resolved FastAPI 0.143.2 and
Starlette 0.52.1. Reviewed P1-04 security updates superseded that pair: the current
lock resolves FastAPI 0.143.3, Starlette 1.8.0, Pydantic 2.14.1,
pydantic-settings 2.16.0, Uvicorn 0.54.0, HTTPX 0.28.1,
Pytest 9.1.1 and Ruff 0.14.0. Runtime/dev dependencies are isolated in `backend/.venv`;
repository tooling retains `requirements-dev.txt`. `uv.lock` records transitive
versions and distribution hashes from public PyPI. Exact compatibility is verified
through locked sync, dependency checking and tests; metadata alone is insufficient.

Starlette is a direct dependency because its middleware/types are used. P1-01's
historical below-1.0 constraint and AnyIO warning were superseded by security
remediation: current constraints are Starlette >=1.3.1,<2 and FastAPI >=0.143.3,<0.144.
The current TestClient emits an upstream HTTPX deprecation warning; do not suppress
it or claim the old constraint still applies. Any dependency update needs focused
compatibility/security review. Mypy 2.4.0 checks app/ in strict mode. This foundation is not an authentication, privacy-compliance,
dependency-vulnerability or production-readiness certification.

Review [approved scope](../docs/REQUIREMENTS.md), [architecture](../docs/ARCHITECTURE.md)
and the [pre-pilot gate](../docs/PRE_PILOT_GATE.md) before expanding functionality.

## PostgreSQL configuration and migrations

See [database operations](../docs/DATABASE_OPERATIONS.md) for role provisioning,
disposable test setup, explicit migration commands and recovery checks. The lock
adds SQLAlchemy 2.0.54, Psycopg/psycopg-binary 3.3.6, Alembic 1.20.0 and
pytest-asyncio 1.4.0. Psycopg's binary extra provides libpq for reproducible local/CI
installation; deployment packaging and TLS infrastructure remain later decisions.
SQLAlchemy's async Psycopg dialect is selected by `create_async_engine`.

`COUNTY_DATABASE_URL` is an optional secret. If absent, live returns 200 and ready
returns a safe 503. An explicitly blank/malformed URL fails startup validation.
Only `postgresql+psycopg` URLs with username, password, host and database are accepted;
optional query keys are `sslmode` and `sslrootcert`. Use URL-encoded credentials.
For non-loopback environments later, require verified TLS under a deployment review.
`COUNTY_MIGRATION_DATABASE_URL` is read only by the migration CLI, with no fallback
to the runtime URL. The runtime settings model does not hold that credential.

| Variable | Default | Bounds / purpose |
| --- | --- | --- |
| `COUNTY_DB_CONNECT_TIMEOUT_SECONDS` | 5 | Integer 2..60; libpq minimum effective timeout is 2 seconds |
| `COUNTY_DB_POOL_TIMEOUT_SECONDS` | 5 | Greater than 0, at most 60; pool checkout |
| `COUNTY_DB_POOL_SIZE` | 5 | 1..20 connections per app process |
| `COUNTY_DB_MAX_OVERFLOW` | 5 | 0..20 extra connections per process |
| `COUNTY_DB_READINESS_TIMEOUT_SECONDS` | 10 | Greater than 0, at most 60; complete readiness operation |

Budget total connections across workers; defaults permit 10 per process. Pools
validate reused connections with pre-ping, hide SQL parameters and disable echo.
Engine/pool diagnostics use the safe application logger; migration diagnostics
are suppressed in favor of generic command outcomes. No global logger is changed.
No connection is opened on import, factory construction or startup. Session
injection creates an independent session and closes/rolls back unfinished work,
including cancellation. Service code must explicitly commit; concurrent tasks must
use distinct sessions. Shutdown disposes pooled connections.

Readiness makes `SELECT 1` and reads at most two rows from
`public.alembic_version`, requiring exactly the single packaged migration head.
Pool wait, pre-ping, queries and connection return share an asyncio deadline;
cancellation cleanup can add a small driver-dependent scheduling delay. Missing,
stale, unknown, multiple or inaccessible revisions return 503, as do missing URL,
authentication failures, outages and timeouts. No readiness results are cached.
Errors preserve the existing request ID/no-store/bilingual envelope and disclose
no database details. Liveness never calls these database checks.

## P2-01 source and security gate

Invite-only backend auth source is prepared behind explicit COUNTY_AUTH_ENABLED.
Runtime/migration/security tests remain pending the changed-exposure decision; no
auth functionality is certified yet. See [identity operations](../docs/AUTHENTICATION_OPERATIONS.md)
and [exposure assessment](../docs/P2_01_EXPOSURE_ASSESSMENT.md) before executing it.
