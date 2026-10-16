# Contributing

Follow [AGENTS.md](AGENTS.md), [development workflow](docs/DEVELOPMENT_WORKFLOW.md)
and [CI gates](docs/CI.md). Coursework outside this checkout is strictly read-only.
Use a dedicated approved branch, meaningful tests and Conventional Commits. Never
commit implementation to main, merge without owner approval or begin the next phase.

## Local checks

Use Python 3.12, uv 0.13.1 and Node 24.22.0/npm 11.19.1. Do not use coursework venvs.
From the repository root, install only the hash-locked CI tools into a local venv:

```bash
python3 -m pip install --only-binary=:all: --require-hashes -r .github/uv-bootstrap.txt
uv venv .ci-venv
uv pip sync --python .ci-venv/bin/python --require-hashes requirements-ci.lock
.ci-venv/bin/python scripts/check_repository.py
.ci-venv/bin/python scripts/check_ci_policy.py
.ci-venv/bin/python -m pytest tests/tooling -q
.ci-venv/bin/ruff check scripts tests/tooling
.ci-venv/bin/ruff format --check scripts tests/tooling
```

Backend checks:

```bash
cd backend
uv lock --check
uv sync --locked
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked mypy
uv run --locked pytest -q -m "not integration"
```

Frontend checks from frontend/:

```bash
npm ci
npm run lint
npm run format:check
npm run typecheck
npm run test:ci
npm run build
npx --no-install playwright install chromium firefox webkit
npm run test:e2e
npm audit --audit-level=high
```

Run real database tests only against explicitly authorized disposable PostgreSQL 17.
The Compose suite provisions its own isolated resources and executes those tests;
see [Compose development](docs/COMPOSE_DEVELOPMENT.md). With frontend dependencies
and Chromium installed, add --browser to scripts/compose_smoke.py to test Nginx.
Do not reuse a developer/coursework database or reset its volume for tests.

## Definition of Done

- Approved scope and observable acceptance criteria are met.
- Behavior-focused tests and all applicable CI checks pass; failures are reported honestly.
- Docs/contracts agree and links/configuration validate.
- Security findings and expiring owner risk decisions remain visible and current.
- No secrets, private datasets, coursework, environments or generated artifacts are staged.
- Actual check names and remote enforcement are verified separately; no false protection claim.
- Owner review is required before merge; working tree is clean after logical commits.

Never introduce a real credential for a scanner test. The scanner self-test uses a
nonfunctional ephemeral pattern, redacts output and deletes its own temporary fixture.
Use a trusted private channel for sensitive reports. Synthetic development approval
is not production approval. No release, deployment or next milestone follows
implicitly from passing checks or merging a PR.
