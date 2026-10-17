# Phase 1 foundation acceptance

Status: automated evidence and ordinary isolated onboarding collected; daily human
CRITICAL review and final owner acceptance remain pending. Phase 1 is not accepted.
Tracking: [issue #7](https://github.com/Abdalla-Wasaa/Production-Grade-County-Government-AI-Assistant/issues/7).
No production, public deployment, real data or Phase 2 authorization.

## Scope and provenance

P1-01 through P1-05 are merged through PR #14. Main baseline is
d5d2b55a7badfcc2764dc6186674a6c1961f9fc2. Ruleset 25222082 is active;
[controlled PR #15](https://github.com/Abdalla-Wasaa/Production-Grade-County-Government-AI-Assistant/pull/15)
verified required-check blocking and passing states, then closed unmerged.
Exact isolated replay candidate: d36a4267aff826f5cc3c05bf5b1168c7f74fe703.
A new HTTPS clone from the official GitHub repository was checked out at that exact
commit in /tmp/county-p106-isolated-checkout. Its initial working tree was clean;
no .env, .local, virtual environments, node_modules, database state or credentials
were copied. Earlier host verification used a separate no-hardlinks clone at
23bb7504183027006c08f3cc83d157f78bd60f58; all host suites were repeated in the new
remote clone at d36a426. Later commits record documentation/evidence only; final-head
hosted results are recorded separately.
No pending result counts as a pass.

## Required acceptance criteria and current evidence

| Issue #7 criterion (original wording) | Verification / current status |
| --- | --- |
| Another clean isolated checkout can reproduce locked setup, baseline migration, local Compose startup and all relevant tests using documentation alone and synthetic data. | Evidenced: clean remote clone, private daemon with no initial images/containers, fresh synthetic secrets/volume; ordinary setup, migration, recovery, persistence and browser replay passed. Host suites repeated; automated container-suite results recorded below. |
| Non-root containers, private PostgreSQL, liveness/readiness, frontend build/lint/types and backend smoke/migration checks have actual recorded evidence matching the approved roadmap exit criteria. | Evidenced by fresh P1-06 hosted PostgreSQL/Compose and build checks at 3ff617b; independent ordinary onboarding also passed at d36a426. |
| English/Kiswahili shell and accessibility observations are documented; no real-county facts, contacts or approvals are fabricated. | Evidenced: 48 candidate and hosted browser/axe cases pass; draft-language and manual pre-pilot reviews remain pending. |
| Documentation links/formatting/security checks and hosted CI are green; all outstanding defects/decisions are explicit. | Initial seven checks and eight archives verified at 3ff617b; final reporting head must also pass. See PR #16 for latest check results; all gaps are explicit. |
| Acceptance report distinguishes implemented foundation from Phase 2/3 capabilities, real-pilot governance and production deployment; no application release/deployment is implied. | Evidenced by this report; owner acceptance/merge and any later phase remain separate decisions. |

## Actual isolation and ordinary onboarding

The first private-daemon attempt on 17 October 2026 used installed Ubuntu Docker
29.1.3, which crashed during initialization. That affected replay was stopped and
its private processes/network resources removed. This was an environment failure,
not an application defect. No existing developer Docker resources were targeted.

A subsequent isolated runtime used the official static Docker 28.0.4 bundle,
matching the hosted runner's working engine version. The bundle SHA-256 was
6b130fa5fb13516620d5ece0b63f63a495cede428bb2f9e24449022e9d72e0cb
([official download](https://download.docker.com/linux/static/stable/x86_64/docker-28.0.4.tgz)).
It was extracted under /tmp without replacing installed tools. Docker and its
containerd 1.7.27/runc 1.2.6 shared a private mount/network namespace, with cgroup v2
visible and enforced. Initial harness attempts had a mismatched containerd shim
PATH and separate mount namespaces; correcting only this disposable harness
resolved them. No application security controls or repository code were changed.

Private daemon ID: 61045b74-588a-4f59-80c1-99c0aaa00ff9.
Its socket/data root were /tmp/county-p106-daemon28/docker.sock and
/tmp/county-p106-daemon28/data. Initial inventory was zero containers and images.
It differs from developer daemon cf92532b-6888-4735-ad89-03c8428b4045
(/var/lib/docker). The empty private Docker client configuration reused no registry
credentials. Public image pulls and synthetic generated Compose secrets were fresh.
HTTP/browser requests ran inside the private network namespace, avoiding the
existing developer's loopback port. Compose 2.40.3 and Buildx 0.30.1 were used.

Ordinary county-dev setup/build/up passed on a fresh private PostgreSQL volume.
Before migration, proxy/liveness returned 200 and readiness safely returned 503;
after explicit and repeated Alembic upgrade/check, readiness returned 200. SQL
confirmed only alembic_version, with no domain tables. Actual UIDs were web 101,
backend 10001 and database 999. Read-only roots, init, capability restrictions,
no-new-privileges, enforced CPU/memory/PID limits and unpublished private database
networking were verified. Database outage preserved liveness/backend process;
recovery restored readiness. Normal down/up preserved the original volume and
revision without reinitialization. The actual Nginx browser replay verified
English/Kiswahili, navigation and /assistant refresh without browser errors.
Graceful ordinary shutdown passed. The administrative SQL harness initially used
an incorrect postgres role; it was corrected to the documented county_bootstrap
role and mounted secret, without printing credentials or altering application code.

The randomized suite completed independently after the ordinary replay, using its
own project/volume and cleaning them up. Ordinary county-dev volume cleanup used
the ownership-checked reset command against the private socket only. No containers
or volumes remained on that private daemon afterward.

Local evidence: /tmp/county-p106-private-full-suite.log,
/tmp/county-p106-private-smoke-images.json,
/tmp/county-p106-private-owned-cleanup.log,
/tmp/county-p106-isolated-start-proof.json,
/tmp/county-p106-isolated-onboarding-success.log,
/tmp/county-p106-ordinary-replay.log,
/tmp/county-p106-ordinary-replay-verified.log and
/tmp/county-p106-ordinary-replay-results.json. These local captures are not durable
GitHub artifacts; hosted archives below provide separately downloadable evidence.

## Verification results

### Fresh-clone host environment and results

Reference environment: Ubuntu 24.04/Linux x86-64, Python 3.12.3, uv 0.13.1,
Node 24.22.0/npm 11.19.1. The host default Node 22.22.3/npm 10.9.8 was not used;
approved Node binaries were explicitly selected. Fresh Python environments and
npm ci were created inside the clone. Download caches/tool/browser binaries may
be reused; no dependency environment, app data or secret state was copied.
The successful private replay used Docker 28.0.4, Compose 2.40.3 and Buildx 0.30.1.
The earlier packaged daemon failure is preserved above. This is not cross-platform evidence.

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
| Ordinary fresh-volume isolated Compose onboarding | Passed at d36a426; startup, migrations, outage/recovery, persistence, isolation, bilingual browser and shutdown |
| Private container test targets | Backend 65 passed; frontend 27 passed |
| Private randomized Compose acceptance | Passed: 12 real PostgreSQL integration cases, one actual Nginx browser case, DDL/revision-write denial, secret canaries, outage/DNS recovery, persistence, shutdown and owned cleanup |

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

The following ordinary commands were replayed against the private daemon at
d36a426. Select that isolated daemon explicitly; never target existing county-dev state:

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
recovery ready=200 and persistence after normal down/up. The actual ordinary Nginx browser check covered bilingual
navigation/refresh; human linguistic/device approval remains separate.
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

All seven required checks passed at hosted evidence commit
3ff617b4a50da9e409abce625ba7c31c30b93ea7. The final reporting commit is documentation
only and must also pass all seven; its actual latest results are recorded in
[PR #16](https://github.com/Abdalla-Wasaa/Production-Grade-County-Government-AI-Assistant/pull/16). No ordinary-onboarding success is inferred from CI.

| Required context | Verified run |
| --- | --- |
| backend-quality | [Backend: passed](https://github.com/Abdalla-Wasaa/Production-Grade-County-Government-AI-Assistant/actions/runs/39018310018) |
| postgresql-integration | [12 real PostgreSQL cases: passed](https://github.com/Abdalla-Wasaa/Production-Grade-County-Government-AI-Assistant/actions/runs/39018310018) |
| python-dependency-audit | [Runtime/dev/tool audits: passed](https://github.com/Abdalla-Wasaa/Production-Grade-County-Government-AI-Assistant/actions/runs/39018310018) |
| frontend-quality | [27 unit / 48 browser-axe / build: passed](https://github.com/Abdalla-Wasaa/Production-Grade-County-Government-AI-Assistant/actions/runs/39018310008) |
| compose-integration | [Container tests, real stack and one Nginx browser smoke: passed](https://github.com/Abdalla-Wasaa/Production-Grade-County-Government-AI-Assistant/actions/runs/39018310027) |
| repository-quality | [Docs/policy/41 tests and 233 subtests: passed](https://github.com/Abdalla-Wasaa/Production-Grade-County-Government-AI-Assistant/actions/runs/39018310005) |
| secret-scan | [Source/history and scanner self-test: passed](https://github.com/Abdalla-Wasaa/Production-Grade-County-Government-AI-Assistant/actions/runs/39018310005) |

Hosted Compose logs report Python 3.12.15, Docker client/server 28.0.4 and Compose
2.38.2; Node/npm checks enforce 24.22.0/11.19.1. These are distinct from the local
failed packaged Docker 29.1.3 attempt; the later successful private runtime used 28.0.4.

The separate [security monitor](https://github.com/Abdalla-Wasaa/Production-Grade-County-Government-AI-Assistant/actions/runs/39018323585) passed all 15
stages at the same commit. Hosted Linux runner jobs provide disposable component
and randomized-Compose automation, distinct from the separately completed ordinary
county-dev replay on the private local daemon. PostgreSQL readiness/migrations,
non-root/private networking, outage/recovery, DNS recreation, secret canaries,
normal-down persistence and graceful cleanup are backed by actual Compose PASS
results. No developer/coursework volumes were targeted.

Eight hosted archives were listed, downloaded and inspected, containing 29 files:

| Artifact | Files | Retention | Hosted archive |
| --- | --- | --- | --- |
| backend-unit-results | 1 | 14 days | [Download/view](https://github.com/Abdalla-Wasaa/Production-Grade-County-Government-AI-Assistant/actions/runs/39018310018/artifacts/12096150159) |
| postgresql-results | 1 | 14 days | [Download/view](https://github.com/Abdalla-Wasaa/Production-Grade-County-Government-AI-Assistant/actions/runs/39018310018/artifacts/12095841925) |
| python-dependency-reports | 3 | 14 days | [Download/view](https://github.com/Abdalla-Wasaa/Production-Grade-County-Government-AI-Assistant/actions/runs/39018310018/artifacts/12094978720) |
| repository-results | 1 | 14 days | [Download/view](https://github.com/Abdalla-Wasaa/Production-Grade-County-Government-AI-Assistant/actions/runs/39018310005/artifacts/12096050459) |
| frontend-reports | 4 | 7 days | [Download/view](https://github.com/Abdalla-Wasaa/Production-Grade-County-Government-AI-Assistant/actions/runs/39018310008/artifacts/12095772458) |
| daily-security-evidence | 12 | 14 days | [Download/view](https://github.com/Abdalla-Wasaa/Production-Grade-County-Government-AI-Assistant/actions/runs/39018323585/artifacts/12096145373) |
| compose-browser | 2 | 7 days | [Download/view](https://github.com/Abdalla-Wasaa/Production-Grade-County-Government-AI-Assistant/actions/runs/39018310027/artifacts/12096140586) |
| compose-evidence | 5 | 14 days | [Download/view](https://github.com/Abdalla-Wasaa/Production-Grade-County-Government-AI-Assistant/actions/runs/39018310027/artifacts/12096045849) |

JUnit case counts/statuses and absence of raw output/property nodes were checked.
Full image reports, inventories, KEV and decision evidence validate; findings are
not suppressed. Artifacts contain expected XML/JSON/public dependency text/HTML,
not .env/credentials/volumes/raw application logs. Successful browser runs do not
produce failure-only screenshots/traces or Compose failure diagnostics.

An extra secret scan of downloaded archives reported four matches: duplicated
public Python signing-key fingerprints in backend image metadata. They match the
original approved image and official Python Dockerfile, not private credentials.
No ignore rule or security-scan suppression was added. Archives expire; rerun CI
when evidence is no longer available rather than treating a dead link as proof.

### Fresh scan snapshot, separate from the approved baseline

Compose scan timestamp: 2026-10-17T08:44:25.704829+00:00 UTC; 2026-10-17T11:44:25.704829+03:00 EAT.

| Runtime | HIGH | CRITICAL | Fixable | Scanned immutable image ID |
| --- | --- | --- | --- | --- |
| web | 0 | 0 | 0 | `sha256:64368fc285a8e5af0358db1523f4521a71c915facae3933fe14a95b803ab0b9e` |
| backend | 44 | 0 | 0 | `sha256:15a93d12dcbc5083d5495178aa7deed950f0c8a22bc824b23ec380f8a393c92a` |
| db | 71 | 3 | 0 | `sha256:2c7409eb75538b1ada7b681bcf53124c6a3f8fdf2bc19cd5d9b6aa01a2573935` |

Both Compose and monitor snapshots retain exactly 115 HIGH/3 CRITICAL occurrences,
zero fixable findings, zero current KEV matches and no policy failures. Counts are
scanner evidence, not confirmed exploitability. Lower severities remain in full
JSON. Database timestamps and catalogue provenance are in the retained decision/KEV
files. These fresh snapshots do not replace or broaden the approved baseline.

### Independent private-daemon scan

The ordinary runtime images at d36a426 were freshly scanned with Trivy 0.76.0,
complete package inventories, current vulnerability metadata and a freshly retrieved
KEV catalogue. Scan time: 2026-10-17T09:06:45.817408+00:00.

| Runtime | HIGH | CRITICAL | Fixable | Immutable image ID |
| --- | --- | --- | --- | --- |
| web | 0 | 0 | 0 | `sha256:1adc16377917381fb2c226a5fe8df387ace1a296a48aca457148680ed7f66852` |
| backend | 44 | 0 | 0 | `sha256:02a6e3361bb5459502adbf5ead0bf07e4bfd4810e91a1e57242ebd89faa9b4c8` |
| db | 71 | 3 | 0 | `sha256:d2fcfc7202cd7f910caf5ab65a6a14516d96fb9d4771f8a044d6dc3fc37ed2d6` |

The strict development policy passed with zero policy failures and no KEV matches.
All 118 approved occurrences remain; no new/fixable/escalated finding was accepted.
Full lower-severity results are retained in the three local image reports alongside
kev.json and decision.json at /tmp/county-p106-private-image-scans. No baseline,
acceptance, suppression or expiry was changed. This adds evidence, not production
approval or a new human review record.

### Repository and coursework boundary

Only Markdown files changed. No application, workflow, dependency lock, migration,
acceptance/baseline or ruleset was modified. The read-only coursework inventory
checked 213646 paths: 213645 match; only module4-capstone/.git/config differs from
the older baseline. Its previously documented modification predates P1-05/P1-06;
it was left untouched. No coursework scripts/dependencies were executed or changed.


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
this agent cannot invent or backdate that review. This pending obligation prevents
an unconditional foundation acceptance recommendation, even with successful isolated
onboarding and automated checks. Final owner review/sign-off is still required.

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
