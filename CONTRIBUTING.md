# Contributing

Follow [AGENTS.md](AGENTS.md), [development workflow](docs/DEVELOPMENT_WORKFLOW.md)
and [CI gates](docs/CI.md). Coursework outside this checkout is strictly read-only.
Use a dedicated approved branch, meaningful tests and Conventional Commits. Never
commit implementation to main, merge without owner approval or begin the next phase.

## Local checks

Use Python 3.12, uv 0.13.1 and Node 24.22.0/npm 11.19.1. Do not use coursework venvs.
From the repository root, install only the hash-locked CI tools into a local venv:

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install --only-binary=:all: --require-hashes -r .github/uv-bootstrap.txt
export PATH="$PWD/.venv/bin:$PATH"
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

## Isolated tool bootstrap and final acceptance

Avoid installing tooling into the system Python or coursework environments. On the
reference Linux x86-64 host with Python 3.12, bootstrap the pinned uv wheel into an
ignored root tooling environment, then install the separately hash-locked CI tools:

Use the root bootstrap commands in Local checks above; uv must report 0.13.1.

The root .venv is tooling only; backend/.venv is independently created by backend
uv sync. Activate approved Node 24.22.0/npm 11.19.1 before frontend commands; a
machine's default Node can be older. Do not force unsupported engines/peer ranges.
The bootstrap wheel is Linux x86-64 specific; other platforms need a separately
verified installation procedure, not a claim of current portability.

Issue #7 criteria require exact-commit fresh-checkout evidence. Keep automated,
manual and unavailable verification distinct in [Phase 1 acceptance](docs/PHASE_1_ACCEPTANCE.md).
Main's seven required checks are enforced by ruleset 25222082, source app 15368.
Owner review still precedes merge and Phase 2. Missing isolated-host or daily human
security review evidence must remain pending; acceptance is never inferred from CI.

For dependency auditing, select the CI-tool interpreter explicitly; the root .venv
only contains uv and does not contain pip-audit/packaging:

```bash
PATH="$PWD/.ci-venv/bin:$PWD/.venv/bin:$PATH" .ci-venv/bin/python scripts/audit_python.py --output .artifacts/python-audit
```

Use checksum-verified Trivy 0.76.0 and Gitleaks 8.30.1 from the reviewed workflow
installation steps when running their commands locally. Do not install arbitrary
latest tools, publish raw diagnostics or treat missing reports as success.
