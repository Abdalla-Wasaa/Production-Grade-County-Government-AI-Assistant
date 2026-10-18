# P2-04 focused exposure assessment — runtime approval pending

## Source and prerequisite

Prepared on 18 October 2026 for issue #20, on
`feat/p2-04-conversation-history-ui`, from main
`a61aa13b1fcede64ce210e43d24c0c248d6ef3c6`.
GitHub PR #26 was verified merged at 2026-10-18T18:31:00Z with all seven required
contexts successful. Clean local main was synchronized with `git pull --ff-only`.
Issue #20 is already closed on GitHub; that historical tracker state is not proof
of UI completion. No GitHub issue/settings changes were made.

Previous accepted exposure:
`88669fbe4cfafc7dc45e6775546e44e6ca8bcbec1dcacfb0f89a36c702af19b4`.
Prepared exposure:
`cd2fd44345bb3b6c09fe05dad6ea0cbe762c866feb8992c6c41c70910ce6f951`.
The Git commit accompanying this assessment identifies the exact source; documentation
is excluded from the exposure digest. No application dependency or lockfile changed.
Backend, migrations, Dockerfiles, Nginx, Compose, workflows and policy records are unchanged.

## Changed attack surface and controls

Protected `/conversations` and `/conversations/:id` now render private, persisted
user content. New forms send authorized create, rename, delete and message requests.
They use the existing authenticated client; guards are UX, not authorization.

The history client checks an opaque account/generation scope before requests and
after response decoding, aborts invalidated requests, and clears private state on
logout/account change. The workspace remounts per scope. Text is rendered through
React, without HTML/Markdown injection or logging. Bearer-only persistence calls
omit cookies, use no-store, reject redirects and inherit coordinated access refresh.
No access/CSRF token, message, draft, history or retry key enters browser storage.

Uncertain message writes retain an identical UUID idempotency key and body in memory
for explicit retry. Concurrent duplicate submits share a request. Reload loses this
memory; a native pending-submission warning and documented inspect-before-resend
procedure reduce accidental duplication but cannot guarantee exactly-once submission
across a browser restart. Rename uses the server ETag and requires explicit reload
on conflict. Metadata is reread after message persistence to avoid stale-title writes.
Pagination is bounded and deduplicated; history is ordered by sequence.

Additional risks include DOM disclosure on shared devices, stale asynchronous data,
XSS through stored content, accidental duplicate writes, destructive user mistakes
and translation/accessibility errors. Source-level controls address these risks;
they are not runtime proof. No new SQL, SQL/XML, SQLite, archive or native parser
operation is introduced. Browser content remains untrusted and backend ownership is
authoritative. Stored-content rendering and mutation behavior require the prepared
negative and real-backend tests before review.

## Static and image evidence

Passed: strict TypeScript, ESLint with zero warnings, Prettier, repository document/configuration validation, Gitleaks current-file scan (no leaks), Git whitespace checks, and runtime-image
build (`docker build --target runtime ... frontend`). The build compiles/bundles
source; the resulting web application/container was not started. No changed app
unit/component/browser/Compose test has executed at this checkpoint.

Fresh npm audit: zero reported vulnerabilities across the unchanged locked tree.
Fresh Trivy 0.76.0 scans targeted immutable IDs for the newly built web image and
unchanged P2-03 backend/PostgreSQL images, with complete package inventories and
no ignore file, severity suppression or ignore-unfixed flag.

| Image | HIGH | CRITICAL | Inventory packages | Available fixes | KEV matches |
| --- | ---: | ---: | ---: | ---: | ---: |
| Web | 0 | 0 | 21 | 0 | 0 |
| Backend | 44 | 0 | 119 | 0 | 0 |
| PostgreSQL | 71 | 3 | 144 | 0 | 0 |
| Total | 115 | 3 | 284 | 0 | 0 |

All 118 reviewed HIGH/CRITICAL occurrence identities and fields match the existing
P2-03 baseline: zero added, removed or changed. All three inventory hashes are
unchanged. See [scan summary](security/p2-04/scan-summary.json) and
[immutable image manifest](security/p2-04/image-manifest.json) for IDs, raw-report
SHA-256 values, inventories, critical rows and comparison results. Raw Trivy JSON,
KEV and fail-closed decision evidence are retained locally under
`/tmp/county-p204-scans/`; those temporary files are not durable hosted artifacts.
The retrieved CISA KEV snapshot is dated 2026-10-16T17:15:48.8752Z. Absence of
scanner/KEV matches does not establish that new source is vulnerability-free.
CVE-2026-77214 remains absent from the remediated web image.

The scanner ran successfully for all three images. The overall policy command
correctly exited 1: the changed application exposure has no current owner risk
decision, so inherited findings lack an applicable acceptance. This is not missing
scan evidence or permission to reuse P2-03 approval. Repository-quality and Compose
cannot be reported green until the separate security decision and normal CI run.

## Three inherited CRITICAL assessments

- CVE-2025-7458, PostgreSQL image `libsqlite3-0` 3.40.1-2+deb12u2:
  crafted SQLite SQL prerequisite; application uses PostgreSQL. No demonstrated API
  exploit. This UI introduces no SQLite execution path.
- CVE-2026-6653, PostgreSQL image `libxml2` 2.9.14+dfsg-1.3~deb12u6:
  authenticated SQL/XML remains a plausible path after SQL access/credential
  compromise. No reproduced exploit; no new XML/SQL endpoint is added by this UI.
- CVE-2023-45853, PostgreSQL image `zlib1g` 1:1.2.13.dfsg-1:
  inherited Debian assessment says vulnerable MiniZip code is excluded from these
  binaries. Scanner occurrence remains visible; no archive-processing feature added.

These remain scanner-reported findings, not independently reproduced exploits.
Local-only exposure does not eliminate them. Existing isolation, least-privilege
roles, loopback bindings, synthetic-only data and no public deployment remain
required; they are not substitutes for remediation or daily human review.

## Prepared validation, not executed

34 focused unit/component cases are prepared: 15 contract boundary cases, 10
transport/session/idempotency cases and 9 UI cases. Coverage includes listing,
selection, create/save, rename/delete, conversation/message pagination, fixed
errors/outage retry, bilingual plain-text rendering, session expiry and late
cross-account responses. Three new Playwright cases run across the existing three
engines (nine planned cases), covering keyboard CRUD/axe, 320px reflow and cross-tab
invalidation. The existing real-backend auth/Compose case now also creates, saves,
reloads, renames and deletes a synthetic conversation.

After owner runtime authorization, run the normal frontend suite:

```bash
cd frontend
npm run typecheck
npm run lint
npm run format:check
npm run test:ci
npm run build
npm run test:e2e
```

Then run `python scripts/compose_smoke.py --browser` from the repository root using
isolated disposable infrastructure. Preserve ordinary evidence sanitation and all
seven hosted check contexts. Manual screen-reader and fluent Kiswahili review remain
outstanding; automated axe is not WCAG certification. No old passing test result is
presented as a result for this source.

## Owner decision required

First authorize isolated synthetic-only unit/component/browser and real-backend
Compose validation of the exact prepared commit and exposure above, including
bounded test-driven corrections within issue #20 and no new dependencies. If source
corrections change exposure, recalculate and follow the existing authorization
procedure before further execution. No security record update is included in that
runtime grant.

After actual runtime evidence, a separately reviewed, exact, time-limited P2-04
security-record decision is needed before push/PR and normal green hosted CI.
Existing P2-03 records and all historical snapshots remain unchanged. Existing
expiry remains **23 October 2026, 23:59 EAT**; all invalidation triggers, scanning,
seven required checks and branch protection remain active. Today's human CRITICAL
review is unconfirmed and must not be invented. No real citizen/county data,
production deployment, automatic acceptance renewal or automatic merge is authorized.

## Authorized validation attempt, 18 October 2026

The owner explicitly authorized isolated synthetic-only frontend, browser,
accessibility and real-backend Compose validation of commit
`c34436487b8bd107fb4f910d3d6a17da1e291d6c`, exposure
`cd2fd44345bb3b6c09fe05dad6ea0cbe762c866feb8992c6c41c70910ce6f951`.
Bounded genuine corrections are authorized, but execution of a corrected exposure
requires stopping and reporting the new hash first. No security-record change,
push, PR, merge, expiry extension or human CRITICAL review completion was authorized.

Actual focused unit/component result: **25 passed, 9 failed, 0 skipped (34 total)**.
All 15 DTO/contract and 10 transport/session/idempotency cases passed. All nine
component cases failed in setup before their assertions: jsdom does not implement
`HTMLDialogElement.showModal`, so spying on the missing method throws. This is test
harness evidence, not nine independent application failures. See
[sanitized unit report](security/p2-04/unit-initial.xml).

The production build passed. Actual focused browser result: **6 passed, 3 failed,
0 skipped (9 total)** across Chromium, Firefox and WebKit. Mobile reflow and
cross-tab invalidation passed in all engines. All three keyboard CRUD cases reached
and passed the axe scan with zero reported violations, then failed the same genuine
focus-return assertion after Escape dismissed the delete dialog. Focus was attempted
while the modal still made its background inert. Final permanent deletion in those
three preview cases was not reached. See
[sanitized browser report](security/p2-04/browser-initial.xml).

These failures are retained as failures. No result is replaced with a passing or
skipped report. Runtime evidence above belongs only to the explicitly tested
commit/exposure, not a subsequently corrected source baseline.

### Real-backend Compose result

The ordinary `scripts/compose_smoke.py --browser` command completed successfully
on the authorized c344364 source. The actual Nginx browser smoke passed (one case),
as did the authenticated real-backend browser case extended with listing, creation,
message persistence across reload, rename, cancel-delete and confirmed deletion.
All 51 real-PostgreSQL regression cases passed, including server pagination.
UI pagination against the real backend was not explicitly exercised with more than
20 rows; the prepared component pagination case remains blocked by the setup defect.
No broader real-browser pagination claim is made.

The full command also verified migration checks, least-privilege runtime access,
non-root/read-only/network isolation, secret canaries, database outage/recovery,
graceful shutdown, proxy recovery and persisted state after down/up. It finished
with test-only cleanup. Only the pre-existing unrelated container remained; it was
not modified. See [Compose browser report](security/p2-04/compose-browser.xml),
[auth/history browser report](security/p2-04/auth-compose.xml) and
[validated image manifest](security/p2-04/validated-runtime-manifest.json).
The full local command log is `/tmp/county-p204-compose.log`. The PostgreSQL
subprocess result is the existing harness's 51-case assertion, not an invented
standalone JUnit report.

### Corrections prepared; new execution checkpoint

- `ConversationDetail.tsx`: return focus in the post-unmount effect after modal
  closure, rather than synchronously in the cancellation handler while the
  background remains inert. The existing three-engine focus assertion is retained.
- `pages.test.tsx`: define the absent jsdom dialog methods only in the test harness
  and restore their original descriptors afterward. Add a focus-return assertion
  to the existing cancellation case. Native browser modal behavior remains real.

Corrected exposure:
`656bd3b5fc48def5402e6e06db69b9a49715b45c69bfea6d96cfcc1a40de7a7a`.
No new dependency, Dockerfile, backend, API or security-policy change is involved.
These corrections have not executed. Strict types/lint/format are rechecked
statically. The earlier passing and failing results remain tied to c344364.

A new owner authorization is required to execute the corrected source: rerun the
focused 34 unit/component cases and nine history browser cases with axe, and the
relevant real-backend UI regression. Existing valid backend/infrastructure evidence
may be reused; do not repeat unrelated suites without a reason. Stop on any further
exposure change before executing its corrected source.

No security acceptance update is appropriate before completing that validation.
After it passes, the anticipated narrow record proposal is
`.github/security-risk-acceptances.json`, a new unchanged P2-03 acceptance snapshot
at `docs/security/p2-04/p2-03-acceptance-snapshot.json`, this assessment,
`docs/SECURITY.md`, and `AGENTS.md`. This is a prospective file list, not approval
to modify those records. Baseline/inventory records need no change if the findings
and inventories remain identical. The final exact source and evidence must be
presented for that separate decision; production remains prohibited and the
23 October 2026, 23:59 EAT expiry cannot be extended by this work.

### Fresh scans of the actual validated runtime images

All three immutable images in the validated manifest were scanned after cleanup.
[Runtime scan summary](security/p2-04/validated-runtime-scan-summary.json) binds
those exact IDs and report hashes to the authorized, tested source, separately
from the corrected source awaiting execution. All three inventories pass the
existing unchanged inventory validator. Findings remain exactly web 0/0, backend
44 HIGH/0 CRITICAL, PostgreSQL 71 HIGH/3 CRITICAL: no added, removed, changed,
fixable or KEV-matching HIGH/CRITICAL occurrence. The scanner's overall exit 1
is the expected unapproved-exposure decision, not an incomplete scan. Raw JSON
and KEV are retained under `/tmp/county-p204-runtime-scans/`. The corrected image
has not been built or run; no claim of runtime validation is made for it.

## Corrected exposure validation, second owner authorization

The owner explicitly authorized synthetic-only runtime validation of
`ea2e8425f8d7a89652cda0ded89eabaadff77e15`, exposure
`656bd3b5fc48def5402e6e06db69b9a49715b45c69bfea6d96cfcc1a40de7a7a`.
No security acceptance update or human CRITICAL review completion was authorized.

Actual results:

- **32/34 unit/component passed; 2 failed; none skipped.** The jsdom setup and
  delete-dialog cancellation/focus test now pass. Remaining failures are test
  fixtures: a regex also matches adjacent date text in another link's accessible
  name; a delayed-header mock holds the serialized auth lock, making the next
  selection wait on an unrealistic unresolved mocked fetch.
- **9/9 browser passed**, three each on Chromium, Firefox and WebKit. All three
  keyboard CRUD flows pass with Escape cancellation, focus return, rename and
  confirmed deletion. All three axe scans report zero violations. Narrow reflow
  and cross-tab clearing pass in all engines. This is not manual WCAG certification.
- **Both actual Compose browser cases passed**: public Nginx routing/language/SPA
  smoke, and real-backend authentication/history CRUD with reload persistence.
  Isolation, least privilege, outage/recovery, shutdown, secret-canary and durable
  state checks also passed. Test resources were cleaned up; unrelated containers
  were untouched. Real-backend UI pagination above 20 rows is still not claimed.
- The **51 earlier passing PostgreSQL cases were reused, not rerun**, as requested.
  The local-only driver verified unchanged backend/test/script/infrastructure paths,
  the exact retained test-image identity and prior successful log checksum. Hosted
  scripts, mandatory commands and checks were not changed. The driver exists at
  `/tmp/county-p204-corrected-compose.py`; it explicitly reports REUSED, not a fresh
  test pass. New local log: `/tmp/county-p204-corrected-compose.log`.

Sanitized actual evidence: [unit results](security/p2-04/unit-corrected-attempt.xml),
[browser results](security/p2-04/browser-corrected.xml),
[Compose browser](security/p2-04/compose-browser-corrected.xml),
[auth/history browser](security/p2-04/auth-compose-corrected.xml),
[validation/reuse summary](security/p2-04/corrected-validation-summary.json), and
[actual runtime manifest](security/p2-04/corrected-runtime-manifest.json).

### Test-only correction and explicit stop

Only `frontend/src/features/conversations/pages.test.tsx` is changed after that
execution. Production application modules remain byte-identical to the tested
source. The pagination assertion now selects the exact title text and verifies its
link destination. The stale-selection fixture returns headers immediately and
streams the old body only after the next conversation is displayed. This exercises
the late-body race without holding the auth lock forever; it retains the assertion
that old content must never be rendered. No assertion, timeout or security control
was removed or relaxed.

New exposure:
`2c8e739185e6f0fc748a4594657ab09978e589563f3464714a7cd97f6aa04996`.
The exposure algorithm includes tests under `frontend/src`, so this test-only edit
changes the digest. Per the owner's explicit condition, the revised tests have not
executed. Static checks are permitted and do not imply passing runtime results.
The next required decision is permission to run the corrected focused component
suite at this exact new commit/digest, reusing the nine passing browser cases and
successful Compose/backend evidence because production code is unchanged.

Final security-record approval remains premature until these two test corrections
are validated. The prospective five-file proposal above is unchanged; no snapshot,
acceptance, baseline or inventory record was modified. All seven hosted checks,
scanning and branch protection remain active, no push/PR was made, and expiry
remains 23 October 2026, 23:59 EAT. Today's human CRITICAL review remains pending.

Fresh Trivy scans of the exact second-run Compose images are recorded in the
[corrected runtime scan summary](security/p2-04/corrected-runtime-scan-summary.json).
All three inventories match the unchanged approved inventory record, and all 118
HIGH/CRITICAL occurrence identities and fields match the prior baseline. No added,
removed, changed, fixable or KEV-matching finding was reported. Counts remain web
0/0, backend 44 HIGH/0 CRITICAL, PostgreSQL 71 HIGH/3 CRITICAL. Raw evidence is in
`/tmp/county-p204-corrected-runtime-scans/`. Overall policy rejection remains the
expected missing approval for changed exposure; it is not a missing image scan.
No zero-new-findings claim establishes that application code is vulnerability-free.
