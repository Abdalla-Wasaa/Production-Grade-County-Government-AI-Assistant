# Local Compose development

This guide began with P1-04 and remains synthetic-only. It does not authorize
production or real county/citizen data, credentials or documents. Current main includes
Phase 2 authentication/private history and domain migrations. P2-05 PR #28 adds
privacy migration 0006; final Phase 2 replay requires its reviewed merge. Ordinary
Compose still defaults to auth disabled. See [the acceptance candidate](PHASE_2_ACCEPTANCE.md)
for the separate authenticated/operator replay and pending operational evidence.

## Prerequisites and first start

Use a Linux Docker Engine with Compose v2 and Buildx, Python 3.12 for the helper,
registry access and a free loopback port 8080. Docker access is privileged host
access; use a trusted personal development machine. Run from the official checkout,
not the surrounding coursework directory. Host Python/Node packages are unnecessary
for container builds. Python 3.12 and Node 24 are pinned inside the build images.

```bash
python3 scripts/dev.py setup
docker compose config --quiet
docker compose build
docker compose up -d
docker compose ps
curl -i http://127.0.0.1:8080/proxy-health
curl -i http://127.0.0.1:8080/health/live
curl -i http://127.0.0.1:8080/health/ready
```

Open `http://127.0.0.1:8080` or `/assistant`. Only web publishes a port, bound to
127.0.0.1. PostgreSQL and FastAPI have no host ports. Do not change this to a public
binding. The setup helper refuses to overwrite credentials; running it again checks
and preserves the existing configuration. It writes a non-secret `.env` (mode 0600)
and `.local/compose` (0700), both ignored. Three independent random passwords and
two role-specific connection URLs live only under the private `secrets` directory.
Never display, commit or attach those files or a process-environment dump.

The generated `.env` includes `COMPOSE_BAKE=false`: Compose 2.40.3's packaged Bake
path panicked with the available Buildx combination during validation. The standard
Compose builder works. The helper also sets this for its subprocesses. This is a
local compatibility workaround, not a change to dependency locking. Avoid inherited
`COMPOSE_*`/`COUNTY_*` overrides with direct Compose commands. Helpers clear those
variables and specify the project, Compose file and environment file explicitly.

To select another local port, deliberately update `COUNTY_HTTP_PORT` in **both**
`.env` and `.local/compose/compose.env` to the same unprivileged port before starting.
Keep the generated project, instance and secret directory unchanged. Setup/reset
refuse divergent copies. Never source either file in a shell or put passwords there.

## Explicit migration gate

A fresh stack intentionally has proxy health 200, liveness 200 and readiness 503.
The backend container can appear unhealthy before migration; this does not restart
it or prevent web from serving. Normal `up` never runs Alembic.

```bash
docker compose --profile maintenance run --rm migrate upgrade
docker compose --profile maintenance run --rm migrate check
curl -i http://127.0.0.1:8080/health/ready
```

Readiness becomes 200 only after PostgreSQL is reachable and the baseline revision
matches. Upgrade is repeatable. `check` is read-only and does not grant permissions.
Upgrade uses the migration role and then grants runtime SELECT on
`public.alembic_version` only. Migration failure exits nonzero with a fixed safe
message. No automatic migration or migration credentials enter the backend.

| Service | Networks | Credentials | Writable paths |
| --- | --- | --- | --- |
| web, UID 101 | edge, application | none | bounded `/tmp` tmpfs |
| backend, UID 10001 | application, database | runtime URL only | bounded `/tmp` tmpfs |
| db, UID 999 | database | bootstrap and two provisioning passwords | named PGDATA volume; bounded tmpfs/socket and shared memory |
| migrate, UID 10001 | database | migration URL only | bounded `/tmp` tmpfs |

Application/database networks are internal. Nginx resolves `backend` using the
container's configured DNS resolver, rechecking after recreation. `/api`, `/api/*`
and `/health/*` retain paths and backend statuses/headers. Unknown API paths return
backend JSON errors, never SPA HTML. `/assets/*` has no SPA fallback. `/proxy-health`
is independent of FastAPI; UI pages remain available during dependency outages.

## Privileges, secrets and initialization

Bootstrap creates fixed synthetic roles only on **empty** PGDATA. The migration
role owns the database/schema, while runtime has CONNECT and schema USAGE, followed
by SELECT on the revision table after explicit upgrade. Runtime cannot create tables
or change the revision. Future application-table grants need a separately reviewed
migration; there are no default blanket grants.

Compose file-backed secrets retain host file modes. Secret files are 0444 so the
specifically mounted non-root UID can read them; the containing host directories
are 0700. This is per-service mount isolation, not encrypted secret storage. Host
administrators, Docker administrators and processes inside an authorized service
are trusted. The launcher loads a URL into its own process environment without
putting it in Docker configuration or command arguments. Do not inspect process
memory/environments or export diagnostic bundles with credentials.

Existing PGDATA is never reinitialized or silently deleted. PostgreSQL's official
entrypoint runs initialization scripts only on an empty data directory. If initial
provisioning fails partway, startup must not be treated as successful provisioning:
retain the volume, inspect safe logs and configuration, and seek review. Never
regenerate passwords against an existing volume. The role creation script fails
closed and suppresses statement/error details that could contain password literals.

## Tests and operational checks

```bash
python3 scripts/dev.py test-backend
python3 scripts/dev.py test-frontend
python3 scripts/compose_smoke.py --report /tmp/county-compose-images.json
```

The first commands build test targets and run unit tests without network access.
The smoke suite builds runtime images and a backend test image, creates its own
random project and credentials, and tests real PostgreSQL migrations, least
privilege, routing, deep-link refresh, 503/200 transitions, secret canaries,
non-root/read-only restrictions, graceful shutdown, recreation/DNS recovery and
volume persistence. Existing PostgreSQL integration tests run in the disposable
database container's loopback network namespace; no host database port is opened.
Cleanup verifies project/instance/disposable ownership labels and deletes **only**
the test project's resources, including its test volume. Runtime images remain for
subsequent scanning. The report contains image references and immutable built image IDs, never secrets. CI also records a test-only ownership
manifest for an always-run fallback cleanup; it rejects normal development and
coursework project names. SIGTERM attempts the same guarded cleanup. A hard kill
can still require review of the recorded test labels; never use global pruning.

```bash
docker compose logs --tail=100 backend web db
docker compose stop db
curl -i http://127.0.0.1:8080/health/ready
curl -i http://127.0.0.1:8080/health/live
docker compose start db
curl -i http://127.0.0.1:8080/health/ready
```

Use those stop/start commands only for this project's synthetic local database.
Readiness becomes safe 503 during outage and recovers without backend restarts.
The API uses bounded readiness/pool/connect timeouts; proxy connect/read/send
limits are 2/15/15 seconds. Restart policy is `no`. Backend has a 20-second graceful
shutdown limit within Compose's 30-second grace period. Nginx receives SIGQUIT.
All services drop capabilities, set no-new-privileges and have bounded CPU, memory,
PID counts and rotating 5 MB logs (three files). See [image review](CONTAINER_IMAGES.md)
for vulnerability findings and refresh policy.

## Persistence, shutdown and guarded reset

```bash
docker compose down
```

Normal shutdown preserves the project-scoped named PostgreSQL volume and local
credentials. Starting again preserves the migrated revision without reapplying it.
Do not use `down --volumes` manually or any global Docker prune command.

```bash
python3 scripts/dev.py reset
```

The helper requires typing exactly `RESET county-dev`, verifies the generated local
configuration and all running/stopped containers, networks and volumes with that
project label, and rejects resources without matching managed/disposable/instance
labels. Only then does it remove this disposable project's resources and volume.
It preserves secret files; the next start initializes a new synthetic database and
needs an explicit upgrade. Wrong confirmation or foreign ownership removes nothing.
It cannot distinguish valuable data placed deliberately in a disposable development
volume: never put real data there. No global cleanup exists.

## Troubleshooting and limitations

- Setup failure: check for an existing, partial, divergent or symlinked local
  configuration. Preserve it and review; there is no automatic repair/rotation.
- Port in use: stop this project's web service or deliberately change both config
  copies as described above. Do not stop unrelated coursework containers.
- Readiness 503: confirm db health, then run explicit migration/check. A fresh schema,
  inaccessible database, wrong credentials or mismatched revision all fail safely.
- Proxy 502 while backend is stopped is expected; UI/proxy health stay available.
  Resolver refresh after backend recreation can take several seconds.
- Registry/build failures need internet access and disk space. Buildx must be
  installed. Docker socket/daemon access is required; no privileged container is used.
- Tested on Linux x86-64, Docker 29.1.3, Compose 2.40.3 and Buildx 0.30.1. Docker
  Desktop, rootless Docker, macOS/Windows bind-mount modes, SELinux and ARM have not
  been verified. Do not claim portability until those environments pass acceptance.
- Local HTTP, private-file secrets and one active county-dev instance per Docker daemon are intentional local
constraints. Separate clones do not isolate this fixed project name; clean
onboarding replay must use a genuinely separate daemon/host. TLS, encrypted managed secrets, backup/restore, production monitoring
  and public deployment remain future approval gates.

## Clean-checkout acceptance and browser smoke

Do not replay ordinary setup from another clone on a daemon already hosting
county-dev. The helper deliberately uses that fixed project name; it does not
provide per-clone daemon isolation. Use an isolated Docker daemon/host with separate
socket, runtime/storage and no existing volumes or credentials. If it cannot start,
stop the affected replay and record it as unavailable; another Compose project on
the shared daemon is not equivalent evidence.

For automated acceptance, the existing smoke suite uses random county-test project
names and fresh volumes. With approved Node/npm, frontend dependencies and Chromium
installed, run from the checkout root:

```bash
python3 scripts/compose_smoke.py --browser --report .artifacts/compose-images.json --cleanup-manifest .artifacts/compose-cleanup.json --diagnostics .artifacts/compose-diagnostics.json
```

This runs the currently collected real-PostgreSQL integration suite and actual Nginx
browser smoke; record actual JUnit counts rather than assuming the historical Phase 1 count. Retain safe reports only, never raw logs, secrets or inspect dumps.
Normal shutdown preserves storage; persistence is not a tested production backup
or restore guarantee. See [Phase 1 acceptance](PHASE_1_ACCEPTANCE.md).
