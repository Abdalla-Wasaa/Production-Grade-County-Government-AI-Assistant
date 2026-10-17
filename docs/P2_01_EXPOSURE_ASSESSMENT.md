# P2-01 changed-exposure assessment and execution gate

Status: source/static preparation only. No changed application, migration or new
backend/PostgreSQL/Compose test has been executed. No implementation PR has been
opened because doing so triggers changed-runtime CI. This document is not risk
acceptance, a test pass, production approval or a vulnerability suppression.

## Authority and candidate

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
