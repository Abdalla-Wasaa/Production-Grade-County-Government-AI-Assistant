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
