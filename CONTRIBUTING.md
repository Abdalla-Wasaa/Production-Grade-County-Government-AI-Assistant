# Contributing

Follow [AGENTS.md](AGENTS.md) and the detailed
[development workflow](docs/DEVELOPMENT_WORKFLOW.md). This repository currently
contains design documents, repository tooling and the P1-01 backend foundation.
Coursework outside this independent checkout is strictly read-only.

## Plan, branch and review

Start with an issue describing the problem, scope, acceptance criteria and relevant
requirement/ADR. Obtain explicit approval before beginning another project phase.
Use a short-lived `feat/`, `fix/`, `docs/`, `test/`, `chore/` or `ci/` branch;
the current workflow setup stays on `docs/phase-0-architecture` as requested.
Never commit directly to `main` after initialization.

Use small Conventional Commits such as `docs(api): clarify retry semantics` or
`ci: validate repository documentation`. Keep unrelated changes separate. Do not
rewrite published history or force-push without explicit approval. Inspect the exact
staged diff before committing; never stage the parent coursework directory.

When authorized to publish, open a PR linked to the issue, explain behavior/design,
attach actual validation results, and describe limitations. A reviewer checks scope,
contracts, security/privacy, tests and maintainability. Resolve blocking comments;
do not claim review or CI execution that did not happen. User approval is required
before merging; a green check alone is not approval.

## Current checks

Use a project-local virtual environment or an isolated tooling environment; never
install into, activate for modification, or run scripts from coursework environments.
From the official repository root:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python scripts/check_repository.py
.venv/bin/python -m unittest discover -s tests/tooling -v
.venv/bin/ruff check scripts tests/tooling
.venv/bin/ruff format --check scripts tests/tooling
git diff --check
git diff --cached --check
```

These commands validate repository tooling/documents. Backend Pytest/Ruff and uv
locked-dependency checks are documented in [backend setup](backend/README.md).
Frontend ESLint/Vitest, migrations, builds and live AI checks arrive in their own
milestones. Add them with meaningful fixtures; never use
empty test suites or skipped jobs as evidence of application readiness.

## Definition of Done

- Scope and acceptance criteria are met; important decisions/tradeoffs are explained.
- Documentation, contracts and diagrams agree; changed links and JSON/YAML validate.
- Relevant tests/checks pass, with exact commands and outcomes in the PR.
- Implementation changes include behavior-focused tests; documentation-only changes
  do not require fake backend/frontend tests.
- No secrets, personal datasets, coursework, virtual environments or build output
  are tracked; inspect staged filenames/content and run secret scanning.
- Security/privacy and bilingual/accessibility impact are assessed where applicable.
- Review blockers are resolved and residual risks are explicit.
- Working tree is clean after logical commits; no unapproved merge, release or phase.

## Security and releases

Never post credentials, citizen records, raw production logs or exploitation details
in public issues. Use synthetic reproductions. Contact the repository owner through
an already trusted private channel for sensitive reports; a dedicated private
reporting channel still needs owner configuration. See [security](docs/SECURITY.md).

Use reviewed semantic versions for application releases, changelog/release notes,
immutable artifact identifiers and tested rollback. No application release/tag is
appropriate for this documentation-only state. See the workflow for release gates,
recommended tools and GitHub settings that still need configuration.
