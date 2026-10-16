# Local PostgreSQL and migration operations

P1-02 implements infrastructure only. PostgreSQL 17 and Python 3.12 are required.
No domain tables, real records, automatic migrations or deployment are authorized.
The only baseline table is `public.alembic_version`, managed by Alembic.

## Roles and configuration

Use distinct database credentials for runtime and migrations. Provision a fresh
local database; do not repurpose coursework databases. Through an administrator's
interactive `psql` session, create roles and set synthetic passwords interactively
with `\password` so values are not stored in SQL history:

```sql
CREATE ROLE county_migrator LOGIN;
CREATE ROLE county_runtime LOGIN;
```

Use `\password county_migrator` and `\password county_runtime` at the psql prompt.
Then run, against a newly provisioned local database only:

```sql
CREATE DATABASE county_local OWNER county_migrator;
REVOKE ALL ON DATABASE county_local FROM PUBLIC;
GRANT CONNECT ON DATABASE county_local TO county_runtime;
```

Connect to `county_local` as its owner/administrator:

```sql
REVOKE ALL ON SCHEMA public FROM PUBLIC;
GRANT USAGE ON SCHEMA public TO county_runtime;
```

The migrator owns the database/schema and can perform reviewed schema changes.
The runtime role is not an owner, superuser, role creator or member of the migrator
role; do not grant database CREATE/TEMP or schema CREATE. It receives CONNECT,
schema USAGE and, after migration, SELECT on the revision table only. Later domain
privileges need their own reviewed migration/operations change.

Provide URL-encoded `postgresql+psycopg` URLs through ignored, purpose-separated
configuration. Use `COUNTY_DATABASE_URL` only for the runtime role. Use
`COUNTY_MIGRATION_DATABASE_URL` only for explicit migration commands. Do not place
both secrets in the application's environment file or pass credentials as CLI
arguments. No dotenv file is discovered automatically. Never echo/export URL values
into logs, screenshots, issue bodies or shell history; use a local secret-aware
launcher or ignored configuration file passed explicitly to uv.

## Explicit migration workflow

From `backend`, with only the migration credential supplied to these processes:

```bash
uv run --locked python -m app.db.migrate upgrade
uv run --locked python -m app.db.migrate check
```

`upgrade` is repeatable and does not change an already-current database. `check`
returns exit status 0 only when the packaged single head matches the stored revision.
Failures return exit status 1 with a generic message, without SQL/credentials or
tracebacks. These are the supported operational commands; raw Alembic errors can
include internal details and should not be shared. `alembic.ini` is credential-free.
Migrations are included in the wheel; source checkout paths are not required.
No migration executes at import, startup, request time or readiness time.

After the first successful upgrade, grant access as owner/administrator:

```sql
GRANT SELECT ON public.alembic_version TO county_runtime;
```

Run the application with only runtime configuration as described in the
[backend guide](../backend/README.md). Check `/health/live` (200) and `/health/ready`
(200 with `{"status":"ok"}` only after migration and the grant). Missing runtime URL
keeps live=200 and ready=503. Stale, unknown, absent, duplicate or inaccessible
revisions and connection failures also produce safe 503 responses.

Keep `0001_baseline` immutable after release. Add new reviewed revisions for future
schema changes; do not edit a released baseline, call `create_all`, stamp an unknown
schema, or auto-upgrade in the app. The current policy requires exactly one packaged
head; branching migration histories must be reconciled before merge. A future
revision introducing domain tables belongs to its separately approved milestone.

## Disposable PostgreSQL 17 acceptance tests

Unit tests deny networking. Integration tests require both explicit authorization
and a loopback administrator URL to the `postgres` control database. Never set these
variables for an existing/shared server. Use a new isolated container with synthetic
credentials, loopback-only published port and no bind mounts or existing volumes.
A local PostgreSQL installation may also be used only if it is explicitly disposable.
Full Docker Compose orchestration remains P1-04.

Example container lifecycle (set `POSTGRES_PASSWORD` privately in the environment
first; its value is never part of the command):

```bash
docker run --detach --rm --name county-p102-test --publish 127.0.0.1:55432:5432 --env POSTGRES_PASSWORD --env POSTGRES_INITDB_ARGS=--auth-host=scram-sha-256 postgres:17
docker exec county-p102-test pg_isready -U postgres
```

Supply `COUNTY_TEST_ADMIN_URL` privately, using `postgresql+psycopg`, the container's
loopback port and database `postgres`. Then from `backend`:

```bash
COUNTY_TEST_DISPOSABLE=YES uv run --locked pytest -q -m integration
uv run --locked pytest -q -m "not integration"
docker stop county-p102-test
```

Fixtures verify PostgreSQL 17 and loopback/control-database configuration before
DDL. They create randomized `county_test_` databases and distinct randomized roles,
then remove only resources they created. Cleanup uses DROP DATABASE WITH FORCE
only for that recorded random database; it never drops/resets the control database.
Tests add a scratch table only inside their disposable database to verify rollback;
that table is not a domain model or migration. Keep test administration credentials
out of the application and its ordinary unit-test environment.

The integration job fails when tests fail. Locally tests skip if no admin URL is
provided; a skipped integration suite is not successful database acceptance. CI sets
both authorization variables and uses a fresh PostgreSQL 17 service. Runtime roles
cannot create tables or update the revision. Migration tests exercise fresh/repeat
upgrade, revision checks, outages/recovery, permissions, timeouts and safe errors.

## Recovery and limits

For a 503, inspect configuration privately, then PostgreSQL availability, role grants
and the explicit revision-check exit status. Correct the actual issue and recheck;
there is no readiness cache. Never expose driver exceptions to clients or blindly
stamp a revision. No automated destructive rollback is provided. Baseline downgrade
contains no domain DDL; future rollback/backup strategy requires review per migration.
Readiness has a complete-operation deadline; asynchronous driver cancellation and
cleanup have normal scheduling latency. Tests bound query and pool exhaustion and
verify connections return to the pool. Long-running domain query deadlines remain
future service requirements, not a global timeout claim.

Compatibility was verified using the locked Python 3.12 environment and real
PostgreSQL 17, following the [SQLAlchemy Psycopg dialect](https://docs.sqlalchemy.org/en/20/dialects/postgresql.html#module-sqlalchemy.dialects.postgresql.psycopg),
[Alembic async recipe](https://alembic.sqlalchemy.org/en/latest/cookbook.html#using-asyncio-with-alembic)
and [Psycopg installation guidance](https://www.psycopg.org/psycopg3/docs/basic/install.html).
Binary driver distributions simplify local/CI setup; review their bundled native
libraries, TLS policy and security updates before any later deployment.

## P1-04 Compose workflow

For the isolated container environment, follow [Compose development](COMPOSE_DEVELOPMENT.md).
No PostgreSQL port is published. The fresh-volume bootstrap creates separate
administration, migration and runtime roles. The explicit maintenance command applies
the existing baseline and grants runtime SELECT on its revision table only. `check`
does not change privileges. Runtime has no domain-table or DDL permissions.
Normal shutdown preserves named storage. Partial initialization is not repaired
automatically; preserve the volume and review safe logs. Never rotate local secret
files against an existing database. Guarded reset deletes only explicitly confirmed,
label-verified disposable project storage, preserves credentials and requires another
explicit migration after reinitialization.
