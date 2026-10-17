# P2-02 frontend authentication: focused exposure assessment

Status: source/static/build preparation only; owner changed-runtime decision pending.
No runtime test, browser result, CI pass or production approval is claimed here.

## Authority and exact source

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
