# P2-02 frontend authentication: focused exposure assessment

Status: isolated synthetic runtime validation authorized by the owner and completed
on 17 October 2026. The source-preparation sections below are historical; the dated
runtime results and updated exposure supersede their pending-test statements.
The owner subsequently authorized the exact five-file P2-02 acceptance update
on 17 October 2026; the final decision section supersedes earlier pending-decision
statements. Hosted CI must be verified on the update commit. No production approval.

Current tested source is 145d562; current exposure is
0b8f2dc7e55e72fbc96325edbec4d57a5a97c9eb52d4fae3251e9aec302b958d.
The dated runtime sections below contain the actual results and exact next decision.

## Source preparation and initial authority (historical)

The owner authorized issue #18 (P2-02 Bilingual frontend authentication integration).
[Backend PR #24](https://github.com/Abdalla-Wasaa/Production-Grade-County-Government-AI-Assistant/pull/24)
merged at ecc9f76a5eda80e23d6ec328881269377cdeb45c, 17 October 2026 14:54:03 UTC,
with all seven required contexts passing on its reviewed head. Clean main was pulled
with --ff-only before creating feat/p2-02-frontend-authentication. Issue #18 was
verified and reopened because implementation remains outstanding. No later milestone
is authorized. Coursework remains unchanged/read-only.

Final application/test source candidate: db32cd731a4b64fb0b5b5668f9c780fa9cec202b.
Later documentation-only commits do not change this source exposure:

| Binding | SHA-256 |
| --- | --- |
| Accepted P2-01 exposure | d82e1a0e6a43f2bea054684dd7e5fad9a2e2fbb96723a93e74f0bde1bf7bfb17 |
| P2-02 exposure | c65d01bdd17de179fce4284328d372aeb23b17b7b49b10e0cd09688c919a6b28 |

The exposure value is computed by the unchanged scripts/security_policy.py.
The exact source commit additionally identifies frontend entry HTML, browser configs
and integration harness changes; the existing hash algorithm does not cover every
repository path. Its coverage was not silently changed in this milestone.

## Changed surface and mitigations

- frontend/src/features/auth/client.ts: same-origin Fetch with no-store, redirect
  rejection, bounded request/lock waits, memory-only access credentials and ephemeral
  CSRF. Every cookie-changing sequence uses one same-origin Web Lock, including a
  fresh CSRF bootstrap inside the lock. No refresh replay grace or blind ambiguous
  retry. Missing Web Locks/BroadcastChannel fails closed. Successful responses are
  checked before their public fields reach React.
- AuthProvider/context/ProtectedRoute: external-store session state, bounded refresh
  timer, visibility revalidation and guarded account UX. The backend remains the
  authority for every user/session/role operation. Guards are not access control.
- LoginPage/ActivationPage/AccountPage: login and one-use activation/recovery,
  acknowledgement of synthetic-v1 notice, explicit separate login after activation,
  current identity, paginated owned sessions, revocation and logout/logout-all.
  No public registration, admin dashboard or another user's session access.
- invitation.ts and frontend/index.html: initial fragment handoff is scrubbed before
  React renders; query tokens are not consumed. Hash changes on the activation page
  are scrubbed too. No analytics, unsafe HTML or telemetry. Fixed return allowlist;
  no caller-provided external redirect. No token in localStorage/sessionStorage/
  IndexedDB or channel messages. HttpOnly cookies remain backend-owned.
- Existing typed en/sw dictionaries, labels, autocomplete, live error summaries,
  focus handling, responsive style and native validation are extended. Unicode
  password length is checked by code points without HTML UTF-16 truncation or
  normalization. Translation remains a development draft pending human review.
- scripts/auth_compose_smoke.py and compose_smoke.py: after auth enablement in the
  already-owned disposable fixture, an additional real browser acceptance uses a
  private 0600 file to hand off fresh synthetic credentials, not CLI/env secret
  values. It deletes the file afterward. Traces/videos/screenshots are disabled for
  auth scenarios. Sanitized auth-compose.xml is checked and included in the existing
  browser artifact. Existing commands, mandatory checks and controls remain intact.

Native browser coordination is a real new capability requirement. Web Locks serialize
cooperating same-origin tabs; they do not eliminate crashes, lost responses, a
compromised same-origin script or requests outside this client. Ambiguous refresh
requires a fresh login; server replay detection remains authoritative. Broadcast
markers can force a local logout but carry no authority, credentials or identity.
A failed server logout clears local state but explicitly warns revocation is not
confirmed; automatic restoration is blocked until login or a successful sign-out.
XSS can still act with a browser session despite memory-only storage and HttpOnly
cookies; no vulnerability-free or perfect confidentiality claim is made.

This makes existing auth APIs usable by an ordinary browser but adds no backend
endpoint, DB privilege, raw SQL/XML/archive processing, public port or live service.
The reviewed three inherited CRITICAL exposures remain:

| Finding | P2-02 delta and uncertainty |
| --- | --- |
| CVE-2025-7458 / database SQLite | No SQLite input or execution path added. No new direct exploit demonstrated; library presence alone proves neither safety nor exploitability. |
| CVE-2026-6653 / database libxml2 | PostgreSQL SQL/XML remains plausible after SQL/database-credential compromise. Browser forms use fixed parameterized backend contracts; no XML/SQL upload route added. |
| CVE-2023-45853 / database zlib | Retain the existing MiniZip applicability qualification and scanner occurrence. No archive/decompression endpoint introduced. |

Non-root/read-only containers, capability/network restrictions, same-origin/CSRF,
synthetic data, operator separation, backend throttles and bounded password work
remain necessary. No real citizen/county data, production credentials or deployment.

## Dependencies and verification status

No package or lockfile changes. The seven dependencies added in P2-01 are inherited,
not new additions here. Build uses the existing Node 24.22.0/npm 11.19.1 toolchain.
TypeScript strict checks, ESLint and production build pass on the prepared source.
Npm audit reported zero vulnerabilities. Ruff validates the changed Python harness.
These commands compile/inspect source; they do not establish runtime behavior.

Prepared but NOT EXECUTED pending authorization:

- Vitest/RTL: restoration, login/activation, errors/CSRF, protected routes, tokens in
  memory only, expiry, two-client serialization, logout/revocation and Unicode input.
- Preview Playwright with explicit mocked API across Chromium/Firefox/WebKit:
  forms, browser reload, concurrent tabs, logout, backend recovery, bilingual axe,
  keyboard and 320-pixel reflow. Mocks are not backend integration evidence.
- Normal Compose --browser: existing foundation/PG tests plus actual Nginx/backend
  browser activation/login, HttpOnly cookies, restoration/automatic refresh, two
  tabs, bilingual axe and current-session revocation. Synthetic fixture only.
- All seven hosted CI contexts. No PR has been opened or runtime CI dispatched.

Manual screen-reader, native-browser and fluent Kiswahili review remain pending.
Normal Compose retains explicit backend auth enablement; the standalone Vite preview
has no backend proxy. Use only the controlled same-origin fixture after authorization.

## Decision boundary

The accepted P2-01 policy does not cover this changed source. Existing acceptance,
baseline, inventory, policy scripts, workflows and ruleset are unchanged. Expiry
remains 23 October 2026 at 23:59 EAT. Daily human CRITICAL review and immediate
invalidation on fixes, new findings, escalations, KEV listings or exposure changes
remain mandatory. Do not fabricate a human review or silently renew/expand scope.

The next request is for isolated synthetic runtime validation and bounded test-driven
corrections within issue #18, with no dependency additions, policy-record updates,
expiry extension, weakened checks, merge or production use. It is not a request to
accept untested code automatically. After actual runtime evidence, any machine-policy
acceptance must be separately bound to the final reviewed source/inventory. Opening
an implementation PR triggers runtime CI and therefore also waits for that authority.


## Final immutable scan evidence — 17 October 2026

Exact candidate reports are in /tmp/county-p202-candidate-scans; manifest is
/tmp/county-p202-candidate-images.json. Scan time: 2026-10-17T15:14:27.898743+00:00.
Fresh retrieved CISA catalogue dateReleased: 2026-10-16T17:15:48.8752Z.
Trivy 0.76.0 uses full package inventory, no repository ignore/config overrides,
and checks immutable image IDs. Metadata freshness checks passed.

| Role | Immutable image ID | Report SHA-256 |
| --- | --- | --- |
| web | sha256:c7b1801e5f1f28c232bc695424fa49df0e089b92bf23d9648e6fdaaa5820b1c3 | a9278d8b7abce331ec41844508a0e0801696488432a3ae95c0c7874bd0ed6b08 |
| backend | sha256:c7e0f3ec51dea0d8059220e16794956dc402b4f1cdcbb1e7f0b3a193e635a303 | 3d4115228f693f91a007f686545d7ccbdc028a23730fce2f6397856bf095fd5b |
| db | sha256:f52049cb7e9fae14fc73d6ed63842489e6aeda9ee855450aecd842167e9731d7 | ca1bc252745209d836a55aa043e02a303855b68aa672e25001d7617355faa0af |

Full reports retain backend **44 HIGH**, PostgreSQL **71 HIGH/3 CRITICAL**, web zero:
**115 HIGH and 3 CRITICAL**, all inherited OS-package/CVE occurrences. Independent
comparison found zero added/removed occurrence keys, severity/vendor-status changes,
available fixes or KEV matches. No duplication or incomplete evidence was accepted.
Scanner matches are not independently demonstrated exploitable vulnerabilities.

All complete inventories match the accepted P2-01 references:

| Role | Packages | Complete inventory SHA-256 |
| --- | --- | --- |
| web | 70 | 7e79131d8a8bfb174b281e86f0f1ecc5495a7df6c29242b0605affe1f2de6682 |
| backend | 119 | 7c9d236e62e9b96b9dfe7ca03dd92b1d999c6bacfb7fb8f67949a9790d88274e |
| db | 144 | f0ff6951e8f3157a9f0e6d15387c68b6e4e591afd21d2d0da972c122ed1ad288 |

The actual unchanged policy command exited nonzero because the approved exposure
hash is still P2-01. Consequently its decision reports absent applicable development
acceptance for inherited findings. This is an expected fail-closed result, NOT a
security-policy pass and NOT scanner failure/missing backend evidence. No current
risk decision is renewed by this report. The old and new package counts/hashes are
identical; source attack surface is changed even with zero new scanner rows.

Actual completed checks: strict TypeScript, ESLint, production build, npm audit
(zero vulnerabilities), Ruff harness lint/format, repository documentation links and
whitespace checks. Formatting/secret scans are repeated on final source/docs before
commit. Builds compile source without starting the app. Unit, browser, actual Compose
and hosted CI results remain pending at the required human runtime gate.


## Authorized runtime validation — 17 October 2026

The owner explicitly authorized isolated synthetic-only frontend unit, integration,
browser/accessibility and backend authentication tests on branch
feat/p2-02-frontend-authentication at 17f03c0, reviewed exposure
c65d01bdd17de179fce4284328d372aeb23b17b7b49b10e0cd09688c919a6b28.
Permission included bounded test-driven corrections without dependencies; it did NOT
authorize acceptance-record changes, expiry extension, merge, production or real data.

Actual test-driven correction, commit 145d562: the real browser test installed its
virtual clock after application timers were scheduled. Its automatic-refresh
assertion failed, although earlier activation/login, cookie, bilingual axe and
concurrent restoration assertions passed. The first overall Compose run therefore
failed and its later acceptance checks were not completed. This result is preserved
in /tmp/county-p202-runtime-compose.log and /tmp/county-p202-first-failure/auth-compose.xml.

The clock now installs before page startup. The test additionally requires HTTP 200
from actual /refresh; no assertion or security control was removed. A unit regression
advances the actual client scheduling timer and confirms the second refresh happens.
Only frontend/e2e/auth-compose.spec.ts and frontend/src/features/auth/client.test.ts
changed; application behavior, all dependencies and locks remained unchanged.
The hash changes because frontend/src includes test files:

**Final tested exposure:** 0b8f2dc7e55e72fbc96325edbec4d57a5a97c9eb52d4fae3251e9aec302b958d.
**Tested source:** 145d562 (application bytes unchanged from approved 17f03c0).

| Actual verification | Result |
| --- | --- |
| Frontend Vitest/RTL | 53 passed, including timer regression; initial 52-case run also passed |
| Preview browser suite | 78 passed across Chromium/Firefox/WebKit, including bilingual axe, keyboard/reflow, restoration, two tabs, revocation and outage recovery; API is mocked here |
| Backend unit/security | 81 passed; 31 integration deselected in that separate run; one pre-existing upstream TestClient deprecation warning |
| Real PostgreSQL integration | 31 passed against fresh disposable DB service through normal Compose command |
| Real Nginx/Compose browsers | One foundation and one complete auth case passed, with real activation/login, HttpOnly cookies, bilingual axe, restoration, automatic HTTP 200 refresh, cross-tab revocation and storage assertions |
| Full Compose acceptance | Passed: all nine API routes, strict refresh replay, CSRF, DB outage/recovery, proxy restart, account/language/revocation persistence after down/up, graceful shutdown and owned cleanup |
| Secret canaries | Passed before and after restart: logs, inspect, history and runtime files |
| Tooling and negative policies | 41 tests and 233 subtests passed |
| Static checks | TypeScript, ESLint, production build, Ruff lint/format (65 files) and strict Mypy (28 backend files) passed |

The final sanitized XMLs have zero failures/skips: frontend .artifacts/vitest.xml
(53), playwright.xml (78), compose-browser.xml (1), auth-compose.xml (1), plus
/tmp/county-p202-backend-unit.xml (81) and /tmp/county-p202-tooling.xml (41).
PG results are asserted from the real container suite's successful 31-test output;
they are not a separate local JUnit artifact. Do not double-count repeated cases.
Preview browser cases were not repeated after the two-file test-only correction:
application bytes and those preview specs were unchanged. The full unit suite and
normal Compose command were rerun because of the new timer regression/failing fixture.

A disposable, network-disabled probe confirmed actual cgroup enforcement:
memory.max=536870912, cpu.max=100000 100000 and pids.max=128. Compose used generated
synthetic credentials, a unique internal network, fresh volumes and loopback-only
web binding; no existing project/DB credentials or data were used. Final project
county-test-86b37ee340a7 containers, volumes and networks were verified removed.
The failed first project was cleaned too. Generated fixture files were deleted.
No coursework or developer services were modified/stopped.

## Final tested-image security delta

Complete reports are /tmp/county-p202-runtime-final-scans/image-{0,1,2}.json,
with kev.json and decision.json; manifest /tmp/county-p202-runtime-final-images.json.
Normal command scripts/scan_images.py was used without suppression or changed policy.
Scan timestamp: 2026-10-17T16:14:49.957453+00:00. Retrieved KEV catalogue dateReleased: 2026-10-16T17:15:48.8752Z.

| Role | Exact tested image ID | Complete report SHA-256 |
| --- | --- | --- |
| web | sha256:5e24ef41ab120e03d88b84d07a7893701a8b1b288e4a859010df7c1cd375c7d9 | 85406f1ac07d87e1c27f9f15be190097d83aa8b36e996e3e8b3e999b5864a022 |
| backend | sha256:dff5ecb0edfc50ff0268c7c6d2336cd696964a42ed2d80e32f41bc94b4229171 | 3f8977063a098fa38b0fcc4f1083360fd087de32851bcee6e0380805b67878b9 |
| db | sha256:483e33cdb4fd350ecba131a3bf0d3b07e714b4fb50394dac13d57f37992f0b2c | fb87dd2acedc9f4efbac9e5a9f36b7332d554e60beac8adcf0858fb50bd22340 |

Fresh full reports retain web zero, backend 44 HIGH and PostgreSQL 71 HIGH/3 CRITICAL:
115 HIGH plus 3 CRITICAL, still 118 exact inherited occurrences. Independently
compared occurrence keys, base pins, vendor status, severity, duplicate inventory,
fix status and KEV matches show no new/removed/escalated/fixable/KEV delta. This
comparison intentionally excludes the missing owner-acceptance requirement for
analysis only; it does not manufacture an accepted policy result.

All full package inventories still match P2-01: web 70,
7e79131d8a8bfb174b281e86f0f1ecc5495a7df6c29242b0605affe1f2de6682;
backend 119, 7c9d236e62e9b96b9dfe7ca03dd92b1d999c6bacfb7fb8f67949a9790d88274e;
database 144, f0ff6951e8f3157a9f0e6d15387c68b6e4e591afd21d2d0da972c122ed1ad288.
No new dependencies; the three CRITICAL assessments above remain applicable.
Zero scanner delta and passing tests do not prove absence of application flaws or
reachability of every binary-library path. The browser enables ordinary interaction
with existing auth APIs; XSS/session and coordination risks above remain relevant.
No direct new SQLite, SQL/XML or archive-execution route was introduced.

Actual policy outcome remains FAIL: the P2-01 decision binds exposure d82e1a0...
and not this tested frontend. The 119 recorded policy failures are one invalid
current decision plus 118 occurrence acceptance failures. Every image scan and full
inventory is valid; no backend evidence-generation failure exists here. Baseline,
inventory, acceptance files and policy/workflow/ruleset controls are unchanged.

## Exact next owner decision (proposal only)

Authorize a separate P2-02 isolated synthetic-development acceptance for the final
0b8f2dc7e55e72fbc96325edbec4d57a5a97c9eb52d4fae3251e9aec302b958d exposure,
unchanged complete inventories and all 118 individually enumerated inherited
occurrences in baseline SHA-256
3b4b2b44866f00c4d24d219b6ee0e4e7428bbc81362af9bc8313e39615c5d234.
Preserve expiry 23 October 2026 at 23:59 EAT, daily human CRITICAL reviews, all
invalidation triggers, synthetic local-only use, production/real-data prohibition,
all seven CI contexts, scanning, branch protection and owner PR review.
No automatic acceptance of future changes or renewal. No human review is forged.

Minimum proposed record/documentation edits AFTER explicit approval:

- .github/security-risk-acceptances.json: new explicitly attributed P2-02 decision;
  retain the existing baseline hash/expiry, bind the exact final tested exposure.
- docs/security/p2-02/p2-01-acceptance-snapshot.json: unchanged byte copy of the active
  P2-01 approval before replacing the active decision; historical approval preserved.
- docs/P2_02_EXPOSURE_ASSESSMENT.md: record the actual owner decision and later CI.
- docs/SECURITY.md: append the separate decision and unchanged restrictions.
- AGENTS.md: record that exact authority and the review/merge boundary.

No baseline, inventory, dependency, policy algorithm, workflow or ruleset changes
are needed. The validator checks every active decision against current exposure;
simply appending a mismatched old decision would still fail. Archiving it separately
preserves history without reattributing or silently extending the previous approval.
After approval, apply only these edits, open the frontend PR linked to issue #18,
and run all seven hosted checks normally. Do not merge. None of these proposed
security-record edits is authorized by isolated validation permission or applied now.
Manual native screen-reader and fluent Kiswahili review remain pending; automated
accessibility is not conformance certification. Production remains prohibited.


Final evidence hygiene: source Gitleaks scan passed. Scanning complete image-report
artifacts flagged two GPG_KEY metadata copies. Each independently matches the public
Python release-signing fingerprint in the
[official image Dockerfile](https://github.com/docker-library/python/blob/master/3.12/slim-bookworm/Dockerfile),
not private key material. Findings were classified, not suppressed; no scanner ignore
or report rewrite was introduced. Auth traces/media were disabled and runtime secret
canaries passed. Final documentation/format/whitespace checks passed. No acceptance,
baseline, inventory, workflow, policy algorithm or ruleset was edited in validation.


## Explicit owner-authorized P2-02 decision — 17 October 2026

The owner explicitly approved the separate P2-02 synthetic-development-only
acceptance for PR #25, tested commit 2a3339410aba6c3037ef349569afffbbae002bd4,
exposure 0b8f2dc7e55e72fbc96325edbec4d57a5a97c9eb52d4fae3251e9aec302b958d,
the 115 HIGH/3 CRITICAL inherited findings, unchanged inventories and residual risks.
The authorization named exactly five files and permitted commit/push and all seven
hosted checks, with no automatic merge. This actual owner decision supersedes the
proposal-only boundary above for this exact candidate; future changes are not approved.

Before replacing the active decision, its complete original bytes were copied to
[the P2-01 snapshot](security/p2-02/p2-01-acceptance-snapshot.json), with byte equality
verified against git show of 2a33394. The active P2-02 decision retains baseline hash
3b4b2b44866f00c4d24d219b6ee0e4e7428bbc81362af9bc8313e39615c5d234 and original expiry
2026-10-23T20:59:00+00:00 (23 October 2026 at 23:59 EAT). Baseline, inventories,
occurrence rows, dependencies, application source, scan policy, workflows and
ruleset remain unchanged. Daily human CRITICAL review is mandatory; no review is
forged by this record. All existing invalidation triggers remain active: available
fix, new finding, severity increase, KEV listing or further exposure/dependency change.
No expansion, renewal, real data, production credentials, public/production deployment
or merge is authorized. The next evidence is the normal seven hosted checks on the
policy-update commit; pending results must not be described as passing.

The failed hosted runs on the previous head are preserved:
[repository](https://github.com/Abdalla-Wasaa/Production-Grade-County-Government-AI-Assistant/actions/runs/39049256726)
and [Compose](https://github.com/Abdalla-Wasaa/Production-Grade-County-Government-AI-Assistant/actions/runs/39049256728).
Repository policy stopped before Pytest, leaving repository.xml absent; the upload
correctly failed. Complete Compose scans and real functional/browser tests passed;
only the applicable owner decision was missing. No fabricated XML, scanner result,
workflow bypass or broad code refactoring is needed to resolve those failures.
