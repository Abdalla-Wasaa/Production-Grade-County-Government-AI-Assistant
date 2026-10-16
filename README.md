# County Government AI Assistant

A production-grade County Government AI Assistant project.

## Project status

Phase 0 and P1-01 through P1-04, including security follow-up PR #12, are merged.
P1-05 strengthens CI quality/security gates and is pending maintainer review. The bilingual assistant is still a placeholder
without messaging or authentication. Kiswahili copy remains pending human review.
Only fictional/synthetic information is authorized.

Start with [Compose development](docs/COMPOSE_DEVELOPMENT.md) and
[container image review](docs/CONTAINER_IMAGES.md). Host-only instructions remain
in [frontend setup](frontend/README.md), [backend setup](backend/README.md) and
[database operations](docs/DATABASE_OPERATIONS.md). The
[real county pre-pilot gate](docs/PRE_PILOT_GATE.md) still applies.

```bash
python3 scripts/dev.py setup
docker compose config --quiet
docker compose build
docker compose up -d
docker compose --profile maintenance run --rm migrate upgrade
docker compose --profile maintenance run --rm migrate check
```

Open `http://127.0.0.1:8080`. Fresh-stack readiness is deliberately 503 until
explicit migration. `docker compose down` preserves database storage. Review the
Compose guide before using the guarded reset command.

## Design documentation

- [Requirements and MVP scope](docs/REQUIREMENTS.md)
- [Architecture and AI boundaries](docs/ARCHITECTURE.md)
- [Database design](docs/DATABASE_DESIGN.md)
- [API specification](docs/API_SPECIFICATION.md)
- [Security and privacy](docs/SECURITY.md)
- [Milestone roadmap](docs/ROADMAP.md)
- [ADR 0001: modular monolith](docs/DECISIONS/0001-modular-monolith.md)
- [Coursework review](docs/COURSEWORK_REVIEW.md)

See [CI gates](docs/CI.md) and the [vulnerability register](docs/VULNERABILITY_REGISTER.md)
for required check contexts, residual risks and expiring development-only acceptance.

## Development workflow

Follow the engineering rules in [AGENTS.md](AGENTS.md). Work on feature branches,
use Conventional Commits, and submit changes through pull requests. User approval
is required before merging or beginning another phase.

See [CONTRIBUTING.md](CONTRIBUTING.md) for local checks and Definition of Done,
and [development workflow](docs/DEVELOPMENT_WORKFLOW.md) for review, tools, CI scope,
security and release gates. CI covers documentation/repository tooling, secret scans
backend locked-dependency/lint/format/tests, frontend checks, and disposable Compose
integration with runtime image vulnerability checks.

## Configuration

The setup helper generates an ignored, non-secret `.env` and private role secrets
under `.local/compose`. Do not replace this with application credentials. See
`.env.example` for the convention and the Compose guide for permissions. Never commit
secret files, environment dumps or database URLs.

Existing AIEngineeringClass coursework is reference material and must remain
unmodified. Do not copy virtual environments or coursework artifacts here.
