# P2-01 changed-exposure assessment and execution gate

Status: separate exact-scope P2-01 owner acceptance authorized on 17 October 2026.
The earlier validation-only gate below is historical; the final decision section
supersedes its blocked policy-record status for the approved candidate only.
The owner explicitly replied: Authorize isolated synthetic validation only.
This authorizes validation and bounded P2-01 test-driven corrections, not acceptance/
inventory/hash edits, expiry extension, production use or merge. The earlier source-
only stage below is historical; subsequent validation evidence supersedes its pending
execution status. Machine-policy approval remains blocked and must not be confused
with permission to run isolated tests. No security finding was suppressed.

## Source-only assessment before runtime authorization (historical)

The following sections through the pre-execution evidence describe the earlier
blocked stage; the dated isolated-validation section supersedes pending test status.

### Authority and candidate

P2-01 issue #17 is authorized. Contract PR #23 merged into main at
980b35d (17 October 2026). The branch is feat/p2-01-account-authentication.
Only backend identity, migrations, tests, necessary schema assertions and docs are
in scope; no frontend source, public registration/email, conversations, AI or cloud.
The final tested/approved candidate must be recorded after actual runtime evidence.
The current exact source candidate and immutable scan image IDs are recorded in the
scan results section once available; no pending result counts as a pass.

## Changed paths and attack surface

- app/modules/identity: strict schemas/settings, Argon2id, allowlisted HS256 JWTs,
  signed CSRF/context tokens, digest-only invitations/refresh lineage, locked
  transactions, shared counters and minimal security audit.
- app/main.py/core config/errors/db session: explicitly enabled auth, safe localized
  denials, body cap, bounded SQL/lock waits and per-request transaction cleanup.
- migrations 0002/0003/0004: six identity tables and restricted runtime grants.
  No startup DDL; 0001 is unchanged. Manual operator/maintenance grants are separate.
- pyproject/uv.lock: Python-3.12-compatible PyJWT 2.15.1, argon2-cffi 25.1.0,
  email-validator 2.3.0 and their locked transitive dependencies. Compatibility was
  resolved and installed without starting the application. Dependency audits are
  recorded separately; installation is not behavioral verification.
- Tests add replay/activation races, claims/CSRF/roles, session ownership, throttles,
  audit rollback, runtime grants and recovery. Existing foundation schema assertions
  now require exactly identity tables; DDL/revision denial remains. No checks/scans
  or workflow/ruleset settings are disabled or renamed.

Nine new routes accept hostile passwords, token strings and identifiers. Previously
only health/readiness probes reached PostgreSQL. The new runtime can create users,
mutate password/version/session state and insert audit/counter rows. HTTP ownership
and role checks are service policy, not a claim of isolation after theft of runtime
DB credentials. In particular INSERT users is required for activation; a fully
compromised runtime/database credential remains a serious residual threat. No HTTP
role/provisioning endpoint or database-role escalation mechanism is introduced.

Native Argon2/CFFI bindings and JWT parsing are new security dependencies. Hashing is
bounded by a per-worker limiter but CPU/memory and worker budgets must be measured
before enabling auth. Shared global and per-IP/account counters use UTC fixed windows;
window-edge bursts and contention need tests/measurement. Password-failure reservations
are released on successful login without clearing other IP failures. Global repeated
throttle denials are audit-aggregated after the first threshold crossing to avoid an
unbounded audit-row flood. This is operational-event aggregation, not scan suppression.

## Existing vulnerabilities and reachability

Existing baseline: backend 44 HIGH, PostgreSQL 71 HIGH/3 CRITICAL, web zero.
These are scanner occurrences, not independently demonstrated exploits.

| CRITICAL | P2-01 exposure change and remaining uncertainty |
| --- | --- |
| CVE-2025-7458 / database libsqlite3-0 | No SQLite API, arbitrary SQL or uploaded SQLite input is added. New authenticated input and DB writes still require review; library presence/absence of a direct route is not proof of non-exploitability. |
| CVE-2026-6653 / database libxml2 | PostgreSQL SQL/XML remains potentially callable after SQL/credential compromise. New queries use parameters and expose no XML/SQL execution endpoint. Increased database privileges are a real change even without direct XML parsing. |
| CVE-2023-45853 / database zlib1g | Retain the scanner row and prior Debian MiniZip applicability qualification. No decompression/upload endpoint is added; no suppression or blanket safe claim. |

All HIGH rows and any new dependency findings remain in complete image reports.
Non-root, read-only roots, capability/network restrictions and loopback topology
remain required; none is proof that local vulnerabilities are harmless. No real data,
production secret, new public port, live integration or payment capability is added.

## Scan and verification evidence

Actual completed static checks: Ruff lint/format, strict Mypy, uv lock/pip compatibility,
repository documentation checks and secret scans (latest outcomes reported with the
candidate). Runtime/dev/tool dependency auditing found zero advisories during source
preparation. Image builds/scans are permitted evidence gathering; no service startup
or application test is implied by an image build. Fresh immutable image results and
KEV/policy outcome must be appended before requesting an exception decision.

Pending: all new unit/security tests, real PostgreSQL migrations/permissions/races,
Argon2 resource benchmark, existing backend/Compose regressions and all seven hosted
checks on changed code. None is marked passed. Operator role setup, offline blocklist
coverage and synthetic secret delivery require validation; no real-pilot approval.

## Exact policy boundary and required human decision

scripts/security_policy.py hashes backend app/migrations/dependencies, frontend and
infrastructure. Changed source cannot match the Phase 1 exposure hash
190b8fd7f0f672432061ca888fd66d6ac7ae4c5ed8a14ec5c72089b5905d1d28.
The existing decision is unchanged: only exact 118 occurrences for synthetic local
development, expiry 23 October 2026 at 23:59 EAT, daily human CRITICAL review and
immediate invalidation on a fix/new finding/escalation/KEV/exposure change.

Source work and nonexecuting scans do not grant runtime permission. Before running
changed-app tests or opening a PR that triggers them, request explicit owner authority
for the concrete changed exposure and synthetic validation scope. Do not modify the
old decision/hash, extend expiry or reinterpret a generic proceed as acceptance.
Even permission to run tests is not itself a machine-policy record: the unchanged
seven-check gate will still reject the exposure hash until a separately authorized
policy-compatible decision or remediation resolves it. If no such decision is
provided, keep source work reviewable locally and mark completion/CI blocked.

No production approval is requested. No vulnerabilities are accepted by this report.

## Actual pre-execution evidence — 17 October 2026

Application/source candidate: 053d9282260cbde8c2751edaaa5077c96d24f0a8.
Exposure SHA-256: 2d29eead8a1aa778633a73f05c38e360d68ef17597f2c7f6eb427066e22af085.
This documentation addendum does not change that application hash. Ruff lint/format
passed (49 files formatted); strict Mypy passed (28 application files); uv lock/pip
compatibility passed (46 installed packages compatible); repository checker passed
(172 files, 49 external coursework links deferred); tooling tests passed (41 tests,
233 subtests); source Gitleaks found no leaks; backend/tool advisory audits found zero.
No new app unit/PG/Compose test, migration or password benchmark was run.

All three images built successfully without starting changed services. Trivy 0.76.0
scan timestamp: 2026-10-17T13:35:50.631702+00:00 (16:35 EAT).

| Role | HIGH | CRITICAL | Fixable | Immutable image ID |
| --- | --- | --- | --- | --- |
| web | 0 | 0 | 0 | sha256:cfd270d351856a71dc16e3a3f8b7e26fb86c1a90d3fcb0b11ed69a30e7285cb5 |
| backend | 44 | 0 | 0 | sha256:e4f8a0e67af54f1231a2184ae2cb9850c6ddafff9de5db6109c75ce58c057475 |
| db | 71 | 3 | 0 | sha256:f52049cb7e9fae14fc73d6ed63842489e6aeda9ee855450aecd842167e9731d7 |

Complete HIGH/CRITICAL occurrence comparison against the reviewed baseline, immutable
image identities and fresh KEV catalogue found no new/changed/escalated/fixable or
KEV-listed occurrence. Counts are scanner findings, not independently proven exploits.
Full lower-severity/package reports remain at /tmp/county-p201-review-scans alongside
kev.json and decision.json; image manifest is /tmp/county-p201-review-images.json.
These are local evidence files, not hosted artifacts or a passing security decision.

The unmodified scanner/policy correctly exits nonzero: exposure acceptance is invalid
for changed code, and backend complete inventory differs. Backend inventory increased
from 112 to 119 packages, adding exactly PyJWT 2.15.1, argon2-cffi 25.1.0,
argon2-cffi-bindings 26.1.0, cffi 2.1.1, dnspython 2.9.0, email-validator 2.3.0 and
pycparser 3.11, with no package removals against the retained Phase 1 report.
New inventory SHA-256: 7c9d236e62e9b96b9dfe7ca03dd92b1d999c6bacfb7fb8f67949a9790d88274e.
The backend raw scan is complete and identity-checked; its policy classification as
invalid evidence reflects that exact-inventory gate, not a claim of scanner success.
The current decision file consequently marks backend status failed and reports 74
unaccepted database occurrences; independently parsing/comparing the full backend
report establishes the additional 44 existing HIGH rows. Never present that raw
comparison as a passing policy result or hide the failed backend classification.

.github/security-baseline.json, security-inventory.json and security-risk-acceptances.json
are unchanged, as are workflows, severity thresholds and ruleset 25222082. No pending
runtime test or CI result is a pass. The smallest next decision is explicit permission
for isolated synthetic P2-01 validation under the unchanged expiry; this alone does
not update policy records or make seven-check CI green. Any later policy-record
change requires its own explicit reviewed authorization; no exception is silently
inherited, broadened or renewed here.

## Isolated validation authorization and results

Application candidate: 3e3a5683ef3cc5c0ff94911c4c4af8de101bd7ef.
Current exposure SHA-256: d82e1a0e6a43f2bea054684dd7e5fad9a2e2fbb96723a93e74f0bde1bf7bfb17.
Compared with the source-only candidate, test-driven changes record operator audit
actors, preserve the exact /sessions/{id} OpenAPI contract, correct the competing-
borrower unit fixture and add actual operator CLI/grant/outage/proxy acceptance.
No eighth dependency, public endpoint, new role or production capability was added.

The isolated Docker 28.0.4 daemon ID is
374a4482-97a0-436d-89c1-b4430e8c6d01, with socket
/tmp/county-p201-daemon/docker.sock and dedicated data/containerd roots. It runs in
its own network/mount namespace and shares neither developer PGDATA nor credentials.
Only prepared/public image layers were imported; DB passwords, volumes, test databases,
roles and host loopback ports were fresh/disposable. Existing coursework and developer
containers were not stopped/reset. Docker/containerd share the private mount namespace;
cgroup v2 is visible/enforced. All HTTP/PG/Compose processes used that private network.
Network-free unit tests use the repository's socket-denial fixtures.

Actual results:

| Verification | Actual outcome |
| --- | --- |
| Combined backend suite | 112 passed: 81 unit/security plus 31 PostgreSQL integration, one existing upstream TestClient warning |
| Final unit/schema run | 81 passed; 31 integration cases intentionally excluded from this separate run |
| Additional real PG operator/maintenance CLI/grants | Passed; real unprivileged roles, exclusive private token handoff, role/disable revocation and audit actors checked |
| Authentication DB outage/recovery | Passed: auth returns safe 503, live remains 200, existing account access recovers |
| Container unit targets | Backend 81 and frontend 27 passed |
| Actual Nginx/Compose auth | Nine-route schema, activation without auto-login, login/me, listing/revoke, refresh/reuse, logout/logout-all and CSRF denial passed |
| Existing Compose foundation | Private non-root/read-only/capability/secret restrictions, explicit migration, 31 real PG cases, browser smoke, outage/DNS recovery, persistence/shutdown and owned cleanup passed |
| Root tooling | 41 tests and 233 subtests passed; not an auth-runtime test count |
| Static checks | Ruff lint/format and strict Mypy (28 app files) passed; source/runtime/tool dependency audits unchanged at zero advisories |

The initial unit run had 80 passes and one test-fixture failure: the limiter was
borrowed by the same task rather than a separate concurrent borrower. Correcting
the fixture exercised the intended WouldBlock/503 path; no capacity limit weakened.
Public role/ownership, password policy, cookie/CSRF and replay semantics are preserved.
The nine-route proxy harness is invoked unconditionally by the existing Compose
acceptance command; no workflow job/check/context was added, removed or disabled.

Backend application benchmark image:
sha256:4477f62c19be0626c4521e3a854ec300a3aad5580cb73d5d592612477e3a58be.
Container UID 10001, read-only root, cap-drop ALL, no-new-privileges, network none.
Actual cgroup memory.max=536870912, cpu.max=100000 100000, pids.max=128 were read
inside the container and asserted. Argon2id memory 65536 KiB, iterations 3,
parallelism 1, one hash borrower per worker: five hash-plus-verify samples had
median 396.54 ms and peak process RSS 110788 KiB (about 108 MiB). This is sizing
on this hardware, not a production latency/load guarantee. The one-entry synthetic
blocklist fixture is not production compromised-password coverage.

Local evidence is in /tmp/county-p201-final-backend.log,
/tmp/county-p201-unit-final.log, /tmp/county-p201-postgresql-extra.log,
/tmp/county-p201-operator-cli.log, /tmp/county-p201-container-unit.log,
/tmp/county-p201-compose-auth.log, /tmp/county-p201-final-tooling.log and
/tmp/county-p201-private/benchmark-final.json. Raw private configs/passwords must
never be copied into review artifacts. Hosted CI results must be recorded from the
PR's actual latest head; no pending or failed security check is claimed as a pass.

The seven contexts and active ruleset 25222082 remain unchanged. Permission to run
validation did not approve/renew the new exposure or package inventory. Therefore
repository policy and complete-image security CI are expected to fail until a
separately authorized, evidence-bound policy-record decision is reviewed. Do not
replace the old hash/inventory/baseline or extend expiry under validation authority.


### Final frozen-source image verification

The final Compose run also verified account/language persistence and continued
session revocation after down/up; post-restart secret-canary checks passed.
The final scan at 2026-10-17T14:10:13Z retained complete, unsuppressed reports.
Fresh CISA KEV catalogue dateReleased was 2026-10-16T17:15:48.8752Z; none of the
reported HIGH/CRITICAL identifiers matched it. An earlier attempt failed to obtain
fresh KEV evidence and was not treated as a security pass.

| Image | Exact final image ID | HIGH | CRITICAL | Available fixes |
| --- | --- | --- | --- | --- |
| Web | sha256:ba35bf46920e0879495e3b3353771217b70969abda70a413161eecc8ab05a371 | 0 | 0 | 0 |
| Backend | sha256:564f320a01f09409b3c2c2602b91a82a663cb7bf6e9839cc3dcf459e8c90b40a | 44 | 0 | 0 |
| PostgreSQL | sha256:2c24800e5f51ab51e3cd4b61955bbe40eb52c96d31424ebe58a5f798d912fc72 | 71 | 3 | 0 |

The scanner reports 118 occurrences, not 118 independently demonstrated exploits.
Backend inventory contains 119 packages and hashes to
7c9d236e62e9b96b9dfe7ca03dd92b1d999c6bacfb7fb8f67949a9790d88274e.
The unchanged policy rejects that inventory and the changed exposure. Consequently
its decision marks backend evidence failed even though the raw JSON is complete
and independently identity-checked. This is not an accepted security result.
Reports are /tmp/county-p201-final-scans/{image-0,image-1,image-2,kev,decision}.json;
Compose output is /tmp/county-p201-final-compose.log. Image IDs differ from the
benchmark's earlier build; benchmark provenance is recorded separately above.
No policy records or expiry were updated. Production remains prohibited.


## Owner-approved policy resolution — 17 October 2026

The owner explicitly approved the seven-file P2-01 synthetic-development acceptance
update for implementation commit 933967ea2a03368677e175f65f6f65dc193a8716,
exposure d82e1a0e6a43f2bea054684dd7e5fad9a2e2fbb96723a93e74f0bde1bf7bfb17,
and backend inventory 7c9d236e62e9b96b9dfe7ca03dd92b1d999c6bacfb7fb8f67949a9790d88274e.
This is actual owner authorization, not an inferred acceptance from green tests.

Original Phase 1 baseline/inventory/decision bytes and SHA-256 values are preserved
in [the historical snapshot](security/p2-01/phase-1-policy-snapshot.json).
The active baseline keeps every vulnerability row and base pin unchanged. Only backend
image identity/report provenance updates to the hosted scan:
sha256:008ab22a737e148330729eb20ef01de16879c87a916fdf91043eaf4aad551387;
report SHA-256 28f237cfdf1608a45a5020be5bc978279ee40f6693671fcc711f4dc01bc0d0c0.
The resulting baseline SHA-256 is
3b4b2b44866f00c4d24d219b6ee0e4e7428bbc81362af9bc8313e39615c5d234.

[Hosted Compose evidence](https://github.com/Abdalla-Wasaa/Production-Grade-County-Government-AI-Assistant/actions/runs/39039792278)
contains complete Trivy 0.76.0 reports (schema 2) for web/backend/db, valid full
inventories and KEV evidence retrieved on 17 October. Backend JSON was present and
valid; its 112-to-119 package mismatch caused the broad diagnostic about missing
scan evidence. No scanner failure or truncated report was demonstrated. The prior
repository exposure guard stopped the shell before Pytest, so repository.xml was
absent, not a malformed report or failed/skipped test result. No fake report or
workflow bypass is needed; rerun existing commands with the authorized records.

The new decision binds all 118 exact inherited occurrence rows: backend 44 HIGH,
PostgreSQL 71 HIGH/3 CRITICAL, web zero. Independently compared keys, severities,
vendor status, fixes and KEV matches have no new/removed/escalated/fixable/KEV delta
in the reviewed reports. Seven added packages remain exactly those listed above.
No vulnerability-free claim follows. Authentication risks and individual CRITICAL
assessments above remain applicable; SQL/XML after compromise remains a plausible
path. Bounded hashing/throttles, parameterized queries, non-root/read-only isolation,
private loopback access and separate DB roles remain necessary compensating controls.

Expiry is unchanged: 23 October 2026, 23:59 EAT (2026-10-23T20:59:00+00:00).
Daily human CRITICAL review remains mandatory, without invented/backdated review.
Immediate invalidation remains required on an available fix, new finding, severity
increase, KEV listing or further exposure/dependency change. No automatic renewal,
real data, production credentials, public/production deployment or merge is approved.
All seven required checks, scanning, branch protection and normal PR review remain
active. The owner authorized normal repository/Compose validation and pushing these
records to existing PR #24; actual hosted results must be checked on the new head.


Local policy-update verification: repository documentation and exposure/workflow
policy checks passed; Ruff lint/format passed; locked CI-tooling suite passed
41 tests and 233 subtests, producing a valid sanitized repository.xml. An initial
invocation in the backend-only environment failed collection for missing PyYAML;
rerunning in the existing CI tooling environment resolved that environment error.
The archived Phase 1 bytes match git show of the approved source commit. All three
existing complete hosted reports pass inventory/finding evaluation against the new
records, with unchanged occurrence rows and base pins. Source secret scanning and
whitespace validation passed. Hosted normal Compose/scans and all seven required
checks must still be verified on the policy-update commit; no pending result is a pass.
