# Phase 1 foundation acceptance

Status: P1-06 verification in progress; owner acceptance is not granted.
Tracking: [issue #7](https://github.com/Abdalla-Wasaa/Production-Grade-County-Government-AI-Assistant/issues/7).
No production, public deployment, real data or Phase 2 authorization.

## Scope and provenance

P1-01 through P1-05 are merged through PR #14. Main baseline is
d5d2b55a7badfcc2764dc6186674a6c1961f9fc2. Ruleset 25222082 is active;
[controlled PR #15](https://github.com/Abdalla-Wasaa/Production-Grade-County-Government-AI-Assistant/pull/15)
verified required-check blocking and passing states, then closed unmerged.
Exact tested documentation candidate: 23bb7504183027006c08f3cc83d157f78bd60f58.
A separate clone was made with git clone --no-hardlinks from the official checkout,
on branch docs/p1-06-foundation-acceptance. HEAD matched that exact commit and the
initial working tree was clean. No .env, .local, backend/.venv or node_modules was
copied. Local results below are for that commit. Subsequent commits reconcile
commands and record evidence only; final-head hosted results are recorded separately.
No pending result counts as a pass.

## Required acceptance criteria and current evidence

| Issue #7 criterion (original wording) | Verification / current status |
| --- | --- |
| Another clean isolated checkout can reproduce locked setup, baseline migration, local Compose startup and all relevant tests using documentation alone and synthetic data. | Pending: isolated ordinary onboarding replay unavailable; host tests and hosted automation recorded separately below. |
| Non-root containers, private PostgreSQL, liveness/readiness, frontend build/lint/types and backend smoke/migration checks have actual recorded evidence matching the approved roadmap exit criteria. | Pending fresh candidate CI results; historical Phase 1 evidence is not this replay. |
| English/Kiswahili shell and accessibility observations are documented; no real-county facts, contacts or approvals are fabricated. | Pending candidate browser results; human review gates remain explicit. |
| Documentation links/formatting/security checks and hosted CI are green; all outstanding defects/decisions are explicit. | Pending final-head checks and downloaded artifacts. |
| Acceptance report distinguishes implemented foundation from Phase 2/3 capabilities, real-pilot governance and production deployment; no application release/deployment is implied. | Report in progress; owner review pending. |

## Actual isolation attempt and unavailable verification

On 17 October 2026 a separate Linux network namespace was created successfully.
A dedicated daemon was configured with a private Unix socket, data/exec roots,
private containerd socket/storage and network. Installed Ubuntu dockerd 29.1.3
crashed during initialization with a nil-pointer/SIGSEGV, both with the selected
classic driver and containerd snapshotter configuration. No functional acceptance
Docker daemon started and no application stack/volume was created there.
This is an environment failure, not a demonstrated application defect.

The affected clean-checkout ordinary Compose replay was stopped. The private
containerd process, namespace, veth and three specifically tagged host networking
rules were removed. No existing Docker resources or coursework container were
stopped, reused or reset. Another project on the shared developer daemon would
not satisfy the requested isolation. A working isolated host/daemon is still needed
to reproduce README setup/migration/outage/persistence commands verbatim.

## Verification results

### Fresh-clone host environment and results

Reference environment: Ubuntu 24.04/Linux x86-64, Python 3.12.3, uv 0.13.1,
Node 24.22.0/npm 11.19.1. The host default Node 22.22.3/npm 10.9.8 was not used;
approved Node binaries were explicitly selected. Fresh Python environments and
npm ci were created inside the clone. Download caches/tool/browser binaries may
be reused; no dependency environment, app data or secret state was copied.
Docker CLI/packaged daemon 29.1.3, Compose 2.40.3 and Buildx 0.30.1 were available;
the private daemon failed as described above. This is not cross-platform evidence.

| Executed check | Actual result at candidate commit |
| --- | --- |
| Hash-verified uv bootstrap and CI-tool sync | Passed in new root .venv and .ci-venv |
| Backend uv lock check/sync/pip check | Passed; 39 installed packages compatible; no lock drift |
| Backend Ruff lint/format and strict Mypy | Passed; Mypy checked 15 app files |
| Backend unit tests | 65 passed; 12 integration cases intentionally deselected; one upstream TestClient HTTPX warning |
| Backend wheel/source distribution | Both built successfully, including packaged migrations |
| Frontend npm ci/tree/audit | Passed; zero reported vulnerabilities |
| ESLint/Prettier/TypeScript/Vitest/build | Passed; 27 unit tests passed |
| Playwright Chromium/Firefox/WebKit plus axe | 48 passed; no human/device approval inferred |
| Tooling/repository/CI-policy/Ruff | 41 tests and 233 subtests passed; 149 repository files validated; 49 external coursework links deferred |
| Python runtime/dev/tool dependency audit | Zero advisories; successful explicit .ci-venv invocation |
| Gitleaks history/current source and engine self-test | Passed; no leaks; synthetic nonfunctional fixture discarded |
| Real Uvicorn process smoke | Missing settings fail safely; no-DB live=200, ready=503; OpenAPI paths exact; graceful lifecycle shutdown passed |
| Mermaid CLI 11.12.0/Chromium | All six architecture/database/roadmap diagrams parsed/rendered and were opened for visual inspection |
| Ordinary fresh-volume isolated Compose onboarding | Not executed: private daemon startup unavailable |

The first manual audit invocation selected the uv-only bootstrap interpreter and
failed with missing packaging; rerunning with .ci-venv and the correct PATH passed.
CONTRIBUTING now names that interpreter explicitly. No dependency or application
code was changed to fix the invocation. The clone's tracked files and locks remain
unchanged after testing. Local console captures/renderings are outside the repo;
publicly reviewable hosted reports are recorded in the next section.

### Reproducible commands

Activate approved Node 24.22.0/npm 11.19.1. From the exact candidate clean checkout:

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install --only-binary=:all: --require-hashes -r .github/uv-bootstrap.txt
export PATH="$PWD/.venv/bin:$PATH"
uv venv .ci-venv
uv pip sync --python .ci-venv/bin/python --require-hashes requirements-ci.lock
.ci-venv/bin/python scripts/check_repository.py
.ci-venv/bin/python scripts/check_ci_policy.py
.ci-venv/bin/ruff check scripts tests/tooling
.ci-venv/bin/ruff format --check scripts tests/tooling
.ci-venv/bin/python -m pytest tests/tooling -q --junitxml=.artifacts/repository.xml
PATH="$PWD/.ci-venv/bin:$PWD/.venv/bin:$PATH" .ci-venv/bin/python scripts/audit_python.py --output .artifacts/python-audit
```

From backend/:

```bash
uv lock --check
uv sync --locked --python 3.12
uv pip check --python .venv/bin/python
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked mypy
uv run --locked pytest -q -m "not integration" --junitxml=.artifacts/unit.xml
uv build --out-dir /tmp/county-p106-backend-dist
```

From frontend/:

```bash
node --version
npm --version
npm ci
npm ls --all
npm audit --audit-level=high
npm run lint
npm run format:check
npm run typecheck
npm run test:ci
npm run build
npx --no-install playwright install --with-deps chromium firefox webkit
npm run test:e2e
```

Browser binaries were already available; the install command is the fresh-host
prerequisite, not a claimed new download in this replay. From root with reviewed
Gitleaks 8.30.1 in PATH:

```bash
python3 scripts/test_secret_scanner.py
gitleaks git --redact --no-banner --log-opts="--all" .
gitleaks dir --redact --no-banner .
git diff --exit-code -- backend/uv.lock frontend/package-lock.json
```

Actual startup smoke used uv run --locked uvicorn app.main:create_app --factory,
loopback-only ephemeral port and --no-access-log with COUNTY_ENVIRONMENT=development.
It asserted curl-equivalent JSON/status/header behavior and terminated only that
server process. Reproduce the ordinary commands using backend/README.md. No DB was
configured; this does not establish migrated readiness or persistence.

The following container commands are the documented replay still awaiting a
functional isolated daemon/host; do not run them against existing county-dev state:

```bash
python3 scripts/dev.py setup
docker compose config --quiet
docker compose build
docker compose up -d
curl -i http://127.0.0.1:8080/proxy-health
curl -i http://127.0.0.1:8080/health/live
curl -i http://127.0.0.1:8080/health/ready
docker compose --profile maintenance run --rm migrate upgrade
docker compose --profile maintenance run --rm migrate check
curl -i http://127.0.0.1:8080/health/ready
docker compose stop db
curl -i http://127.0.0.1:8080/health/ready
curl -i http://127.0.0.1:8080/health/live
docker compose start db
curl -i http://127.0.0.1:8080/health/ready
docker compose down
docker compose up -d
docker compose --profile maintenance run --rm migrate check
```

Expect fresh live=200/ready=503, migrated ready=200, outage live=200/ready=503,
recovery ready=200 and persistence after normal down/up. Check UI bilingual
navigation/refresh manually; do not claim these ordinary replay steps occurred.
The existing randomized automated smoke is distinct:

```bash
python3 scripts/dev.py test-backend
python3 scripts/dev.py test-frontend
python3 scripts/compose_smoke.py --browser --report .artifacts/compose-images.json --cleanup-manifest .artifacts/compose-cleanup.json --diagnostics .artifacts/compose-diagnostics.json
python3 scripts/scan_images.py .artifacts/compose-images.json --output .artifacts/image-scans
python3 scripts/security_monitor.py --output .artifacts/monitor
```

These require a functional Docker daemon and reviewed tool prerequisites. Hosted
execution, suite counts and scan results must be verified below, not inferred.

### Hosted candidate verification

Pending the P1-06 PR run and actual artifact download. No ordinary-onboarding
success is inferred from CI, even when hosted component/Compose checks pass.

## Automated versus manual evidence

Browser automation and axe test English/Kiswahili rendering, navigation, keyboard
behavior and reflow. They do not establish translation quality, screen-reader
conformance, physical-device behavior or native-browser zoom approval. Those
[pre-pilot gates](PRE_PILOT_GATE.md) remain pending and do not authorize real users.
No current frontend API consumer exists: only the proxy infrastructure can route
operator/test requests to backend health/error/OpenAPI paths. Auth and chat are absent.

## Security and acceptance decision

Approved unresolved baseline: backend 44 HIGH; PostgreSQL 71 HIGH/3 CRITICAL; web
zero. These are scanner package/CVE occurrences, not independently demonstrated
exploits. Current baseline/acceptance files must stay unchanged. Existing acceptance
is synthetic-local-development only and expires 23 October 2026 at 23:59 EAT.
No renewal or expansion is authorized. Stop acceptance on new, changed, fixable,
escalated or KEV-listed findings; preserve complete reports and timestamps.

Daily human CRITICAL review is owned by project owner Abdalla-Wasaa. No actual dated
human review reference was provided for this report: status pending. Automation or
this agent cannot invent or backdate that review. This pending obligation and the
unavailable isolated onboarding evidence prevent an unconditional foundation
acceptance recommendation, even if all automated checks pass.

Production security approval: not granted. Public deployment, real county/citizen
records, production credentials, live integrations and paid/live AI remain forbidden.
Technical foundation acceptance would be restricted development only and requires
owner review of the actual remaining conditions. Issue #7 stays open until that
final acceptance; a PR must not automatically close it.

## Phase 2 handover proposal

After explicit Phase 1 acceptance and separate Phase 2 approval, review the existing
identity/conversation/API/database contracts and invitation delivery decision.
Phase 2 may introduce users/conversations/messages and secure sessions through
separate reviewed migrations, ownership/CSRF/rotation/concurrency tests and bilingual
history UX. No provider dispatch, RAG or tools are brought forward. No Phase 2
branch, code, account provisioning or deployment is authorized by this report.
