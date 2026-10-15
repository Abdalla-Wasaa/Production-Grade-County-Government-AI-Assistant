# Development workflow

Status: repository engineering setup, 2026-10-15. The project has no application
implementation. This workflow supplements [AGENTS.md](../AGENTS.md),
[CONTRIBUTING.md](../CONTRIBUTING.md), [roadmap](ROADMAP.md), and
[security requirements](SECURITY.md). Setup does not authorize Phase 1 or a merge.

## Repository boundary

The independent checkout is
`/root/AIEngineeringClass/afyaplus-ai-week1/Production-Grade-County-Government-AI-Assistant`.
It has its own `.git` directory and the official origin:
`https://github.com/Abdalla-Wasaa/Production-Grade-County-Government-AI-Assistant.git`.
Its location inside the coursework parent does not make the parent the Git root.
Always work from this checkout; never initialize Git in the parent, move the
checkout, copy coursework projects or rewrite history without approval.

Before work, inspect:

```bash
pwd
git rev-parse --show-toplevel --absolute-git-dir
git branch --show-current
git status --short --branch
git remote -v
git log -5 --oneline
git ls-files
```

Coursework paths cited by [the review](COURSEWORK_REVIEW.md) are reference links,
not vendored/tracked files. CI explicitly reports these links as external/deferred:
GitHub runners do not have the private local coursework tree. All other local
documentation links must stay inside this checkout and resolve to repository files.

## Issue to branch to pull request

1. Identify the approved milestone and open a scoped issue when publication is
   authorized. Use the bug/feature forms, requirement IDs, acceptance criteria,
   test plan and data/security implications. An issue is not phase approval.
2. Start a short-lived feature branch from current reviewed main after an authorized
   fetch; use names such as `feat/conversation-history`, `fix/session-expiry`,
   `docs/api-contracts`, `test/ownership`, `chore/dependencies` or `ci/docs-checks`.
   This setup is explicitly performed on existing `docs/phase-0-architecture`.
3. Make focused changes and tests. Inspect `git diff`, stage explicit paths, inspect
   `git diff --cached --name-only` and `git diff --cached`, then commit.
4. Use Conventional Commits: `type(scope): imperative summary`; types include
   `feat`, `fix`, `docs`, `test`, `refactor`, `build`, `ci`, `chore`, `perf` and
   `revert`. Document a breaking contract with `!` and a `BREAKING CHANGE:` footer.
   Reference issues truthfully; do not claim unperformed testing or review.
5. Run applicable checks. When authorized, push the feature branch and open a PR
   using the template. Include problem/result, evidence, tradeoffs and residual
   risks. Prefer small reviewable diffs; do not merge unrelated dependency upgrades.
6. Request review. Reviewers assess ownership, contracts, failure paths, tests,
   security/privacy, bilingual UX and documentation. Distinguish blocking findings
   from optional suggestions. Resolve blockers and rerun affected checks.
7. Merge only after explicit user approval, green required checks and resolved
   review. Recommended default is squash merge with a Conventional Commit title;
   preserve individual commits when their history is useful and approved. Delete
   merged branches only when authorized. Never infer next-phase approval from merge.

Do not commit directly to main after initialization. Reconcile conflicts carefully
on the feature branch and test resulting behavior. Never manufacture conflicts,
silently discard changes, force-push, rebase published history or move repository
boundaries without explicit approval. There are no automatic merge/deploy steps here.

## Tools and staged adoption

| Tool | Purpose | Current activation / future gate |
| --- | --- | --- |
| [Ruff](https://docs.astral.sh/ruff/) | Python linting and formatting | Active only for repository-check tooling; backend configuration arrives with Phase 1 |
| [Pytest](https://docs.pytest.org/en/stable/) | Backend policy/API/integration tests | Add with backend implementation; no empty backend test job now |
| [ESLint](https://eslint.org/docs/latest/use/getting-started) | React/TypeScript linting | Add with frontend package and configuration |
| [Vitest](https://vitest.dev/guide/) | Frontend unit/component testing | Add with Vite frontend and meaningful component tests |
| [GitHub Actions](https://docs.github.com/en/actions) | Automated review gates; approved deployment later | Current workflow validates documentation/tooling and scans secrets only |
| [Mermaid CLI](https://github.com/mermaid-js/mermaid-cli) | Parse and render Markdown diagrams | Local explicit diagram validation; CI checks fenced blocks but does not render them |
| [Gitleaks](https://github.com/gitleaks/gitleaks) | Secret-pattern scanning of history and working files | Pinned scanner job; no guarantee that every credential or private dataset is detectable |

Current `requirements-dev.txt` installs tooling dependencies only. Use a new `.venv`
inside this project or an isolated `/tmp` environment. Do not reuse/modify coursework
venv, install app dependencies prematurely, or run coursework scripts. Versions are
explicit pins; dependency refreshes require review, scanning and rerun checks.
Do not copy whole coursework implementations; use the documented patterns.

## Current checks and their limits

Run the commands in [CONTRIBUTING.md](../CONTRIBUTING.md). The checker uses Git's
tracked plus nonignored new files, validates UTF-8/LF/final newline/trailing space,
conflict markers, Markdown headings/fences/inline file links, fenced JSON, YAML
syntax and issue-form essentials, workflow read-only permissions/action SHA pins,
and forbidden tracked artifacts. It is a scoped validator, not a complete CommonMark,
GitHub Actions schema, external URL availability or application security audit.

Tooling regression tests exercise rejection of malformed JSON/YAML, missing and
escaping links, formatting problems, unsafe workflow pins and forbidden artifacts.
CI runs these tests with standard-library unittest. This is repository tooling
verification, not backend Pytest coverage. CI executes on pushes, PRs and manual
dispatch, with timeouts, read-only contents permissions and no provider/deployment
secrets. Checkout credentials are not persisted. Full-SHA action pins follow
[GitHub security guidance](https://docs.github.com/en/actions/reference/security/secure-use).
No `pull_request_target` execution of untrusted PR code is used.

The Gitleaks job scans full checked-out Git history and current files, redacts
findings and fails on detected secrets. Its downloaded Linux archive is checked
against a committed SHA-256; never replace a pin without verifying the official
release. Local scan reports/rendered diagrams remain in `/tmp`, not in Git. Private
datasets require human staged-file review even if a scanner is green.

For diagrams, extract each `mermaid` fence and render it with Mermaid CLI 11.12.0
using a compatible Chromium in an isolated tooling directory. A successful renderer
run verifies syntax and output generation; opening the generated images is a
separate visual check. GitHub's renderer may use a different Mermaid version, so
review the PR preview after publication is approved. Do not install Node packages
or generated diagrams into coursework folders.

Future implementation PRs add Ruff/Pytest backend jobs, ESLint/Vitest/frontend build,
PostgreSQL migration/ownership/concurrency tests, provider-fake evaluation and
dependency/image scans when their inputs exist. Live API tests remain opt-in and
budget-limited; synthetic fixtures are the default. No present check claims the
future application has passed tests.

## Definition of Done and release management

Use the [contribution checklist](../CONTRIBUTING.md). In addition to feature
acceptance, record actual check results and unresolved risks; update ADRs/contracts
when behavior changes; verify no secrets/coursework/generated assets are staged;
obtain review and user approval before merge. Keep commits small and finish with a
clean working tree. User approval is also required before starting another phase.

No application release is created for Phase 0. When implemented, use semantic
versioning (MAJOR incompatible contract; MINOR compatible feature; PATCH compatible
fix), a reviewed changelog, immutable image/source identity, evaluated prompt/model/
corpus versions, migration plan and tested rollback. Pre-1.0 breaking behavior must
still be explicit. Tag only an approved reviewed commit; prefer signed annotated
tags and record signing limitations. Release notes distinguish local tests, CI,
live evaluations, migrations and deployed verification. Revert/forward-fix through
a reviewed branch instead of rewriting main. Production deployment later requires
protected environments, privacy/hosting approval and the roadmap's restore/incident
gates; a tag does not authorize deployment.

## GitHub settings requiring owner action later

Recommend a main ruleset requiring PRs, resolved conversations and the current
`Documentation / validate` and `Documentation / secrets` checks after their first
successful hosted run. Block force pushes/deletion; avoid routine bypass. Require
one independent approval when another eligible maintainer exists. GitHub does not
allow authors to approve their own PR, so a solo-maintainer review policy needs an
explicit owner decision; do not fabricate approval or silently bypass protection.
Enable available secret scanning/push protection and a private vulnerability channel.
Consider CODEOWNERS when real responsible reviewers are identified.

No branch rules, collaborators, release settings, private reporting channel or
deployment environments are configured by these local files. CI has not run on
GitHub until publication is approved. Current action: stop after local validation
and commits; no push, PR, merge, release or next-phase implementation.

## Setup validation record (2026-10-15)

- Confirmed independent Git root and local `.git` directory, official HTTPS origin,
  clean starting branch `docs/phase-0-architecture`, and five existing commits.
  Starting tracked files were the 12 expected project documentation/scaffolding
  files; no coursework files or submodule entries were tracked.
- Document/GitHub configuration validator and eight tooling regression tests passed.
  Ruff 0.14.0 lint/format checks and Git whitespace checks passed.
- Gitleaks 8.30.1 checked all local Git refs/history and current repository files
  with redacted output; no leaks detected. This does not certify data privacy or
  replace human review of staged content.
- Mermaid CLI 11.12.0 generated PNGs for both architecture diagrams, the database
  ER diagram and roadmap. A semicolon in a sequence message label was corrected
  because it caused a real parser error. All four then parsed/rendered successfully
  and their images were visually inspected for readable labels and connections.
- Rendering used isolated `/tmp` dependencies and an existing Chromium; generated
  files remain outside the repository. The temporary CLI dependency tree reported
  a deprecated Puppeteer version; it is not a project/runtime dependency. A future
  committed renderer setup needs a reviewed supported dependency lock.
- GitHub-hosted checks, GitHub diagram previews and branch-rule enforcement remain
  unverified because no push, PR or remote-settings mutation is authorized.
