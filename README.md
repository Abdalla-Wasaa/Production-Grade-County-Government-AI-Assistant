# County Government AI Assistant

A production-grade County Government AI Assistant project.

## Project status

Phase 0 documentation is merged. P1-01 provides the local synthetic-development
FastAPI backend foundation, pending PR review; no chatbot features are implemented.
See [backend setup and checks](backend/README.md) and the
[real county pre-pilot gate](docs/PRE_PILOT_GATE.md). Other Phase 1 issues require
separate approval; no database, frontend, AI integration or deployment exists yet.

## Design documentation

- [Requirements and MVP scope](docs/REQUIREMENTS.md)
- [Architecture and AI boundaries](docs/ARCHITECTURE.md)
- [Database design](docs/DATABASE_DESIGN.md)
- [API specification](docs/API_SPECIFICATION.md)
- [Security and privacy](docs/SECURITY.md)
- [Milestone roadmap](docs/ROADMAP.md)
- [ADR 0001: modular monolith](docs/DECISIONS/0001-modular-monolith.md)
- [Coursework review](docs/COURSEWORK_REVIEW.md)

## Development workflow

Follow the engineering rules in [AGENTS.md](AGENTS.md). Work on feature branches,
use Conventional Commits, and submit changes through pull requests. User approval
is required before merging or beginning another phase.

See [CONTRIBUTING.md](CONTRIBUTING.md) for local checks and Definition of Done,
and [development workflow](docs/DEVELOPMENT_WORKFLOW.md) for review, tools, CI scope,
security and release gates. CI covers documentation/repository tooling, secret scans
and backend locked-dependency/lint/format/tests. Frontend checks begin with P1-03.

## Configuration

`.env.example` documents configuration placeholders. Keep real credentials in
local environment variables or an ignored `.env` file. Never commit secrets.

Existing AIEngineeringClass coursework is reference material and must remain
unmodified. Do not copy virtual environments or coursework artifacts here.
