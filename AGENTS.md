# Persistent engineering rules

- Use professional modular architecture with clear responsibilities and boundaries.
- Follow Conventional Commits for all commits.
- Work through feature branches and pull requests.
- Never commit directly to `main` after the initial repository initialization commit.
- Never expose secrets or credentials in source code, commits, logs, or documentation.
- Never modify existing AIEngineeringClass coursework. Treat coursework outside this
  official repository as read-only reference material; authorized work within this
  repository is permitted even though it is located inside the coursework directory.
- Add tests for implementation changes and run the relevant checks before review.
- Explain important design decisions and their tradeoffs in reviewable documentation
  or pull request descriptions.
- Require the user's explicit approval before merging or beginning another phase.

## Current scope

The owner explicitly approved P2-05 engineering policy and source implementation
on feat/p2-05-privacy-lifecycle after merged PR #27 (main a7902700e10dcd6fc71ebf582ba84fada1d93254).
Preserve existing retention, add audited authorized holds, verified operator account
requests, bounded purge/catch-up and focused tests. No new public admin API,
LLM/RAG/payment work, real data or production deployment.

Prepare the implementation/tests before the runtime checkpoint. Before executing
changed application code, report exact commit/exposure, complete dependency/scan
delta and stop for explicit isolated synthetic authorization. The P2-04 acceptance
is not inherited. Do not modify security-risk/baseline/inventory records or snapshots
without separate explicit approval. Preserve all seven checks, scanning, branch
protection, expiry 23 October 2026 at 23:59 EAT and all invalidation triggers.
Today's actual human CRITICAL review remains unconfirmed. No fabricated reviews.
No push/PR until authorized testing and any separate security-record decision;
no automatic merge or Phase 2 closure. Prior pending statements below are historical.

## Historical acceptance

P2-03 security records remain unchanged. The approved exposure is
88669fbe4cfafc7dc45e6775546e44e6ca8bcbec1dcacfb0f89a36c702af19b4,
with 115 HIGH and 3 CRITICAL inherited occurrences and the remediated web image.
The previous P2-02 policy is preserved byte-for-byte in
`docs/security/p2-03/p2-02-policy-snapshot.json`. See
`docs/P2_03_EXPOSURE_ASSESSMENT.md` for the prior validation and review limitations.
This historical approval does not authorize the P2-04 exposure.

## P2-04 controlled validation and correction checkpoint

The owner authorized isolated synthetic frontend/browser/Compose validation of
c34436487b8bd107fb4f910d3d6a17da1e291d6c with exposure
cd2fd44345bb3b6c09fe05dad6ea0cbe762c866feb8992c6c41c70910ce6f951.
That run is complete: unit/component 25 passed and 9 setup failures; browser
6 passed and 3 keyboard focus failures; real Compose/auth/history flow and all
51 PostgreSQL cases passed, with disposable cleanup verified.

Two bounded corrections are prepared: jsdom modal-method shims with restoration,
and focus return after modal unmount instead of while the background is inert.
Corrected exposure is
656bd3b5fc48def5402e6e06db69b9a49715b45c69bfea6d96cfcc1a40de7a7a.
The owner explicitly requires stopping before executing changed application code
when corrections change exposure. Do not execute this corrected source until that
new runtime authorization arrives. Static checks are permitted. Do not infer
security acceptance, push/PR authorization or daily human CRITICAL review from the
prior runtime grant. All historical approvals, expiry and controls remain unchanged.

## Second runtime grant and test-only checkpoint

The owner authorized ea2e8425f8d7a89652cda0ded89eabaadff77e15 / exposure
656bd3b5fc48def5402e6e06db69b9a49715b45c69bfea6d96cfcc1a40de7a7a.
Actual result: 32/34 unit/component pass; all nine browser cases and both real
Compose browser cases pass; existing 51-case PG result reused with source/image/log
verification. Cleanup completed. Two remaining fixture defects were corrected only
in pages.test.tsx; production application modules did not change.
New test-inclusive exposure is
2c8e739185e6f0fc748a4594657ab09978e589563f3464714a7cd97f6aa04996.
Stop before executing the edited tests until the owner authorizes this new hash.
Do not rerun unchanged browser/backend suites without a reason. Security-record
approval, push/PR, merge and today's human CRITICAL review remain ungranted.

## Owner-approved P2-04 security decision — 19 October 2026

The owner explicitly approved this five-file update on 19 October 2026.
This current authorization supersedes earlier pending checkpoint instructions. Reviewed commit 95f5ed0c57bc9ca72abf457ecc99f09b63e2d3b1; tested implementation
f6e65c1a1bbd927114458c57282823a6468392d7; unchanged exposure
2c8e739185e6f0fc748a4594657ab09978e589563f3464714a7cd97f6aa04996. Validation is 34/34 focused unit/component, 9/9 browser cases and
three axe scans, plus successful real Compose and verified reuse of 51 PG cases.
The exact 115 HIGH/3 CRITICAL inherited occurrences and all inventories are unchanged.
Previous P2-03 acceptance bytes are preserved at
`docs/security/p2-04/p2-03-acceptance-snapshot.json`
(SHA-256 cc17ab3f70fe52220d57dba875f846c09daa9c77a0b8226412c5c47e50b3aa11). No baseline or inventory update is authorized.

Acceptance is only for isolated synthetic development through 23 October 2026,
23:59 EAT. Production/public deployment, real citizen/county data and production
credentials remain prohibited. Daily human CRITICAL review remains required and
pending; this decision does not record review completion. Fix/new-finding/severity/
KEV/exposure/dependency invalidation triggers, all seven checks, complete scans,
branch protection and owner PR review remain mandatory. After this explicit record
approval, publish the branch/PR linked to issue #20 and run normal hosted CI.
No automatic renewal, future exposure approval, merge or P2-05 implementation.

## P2-05 authorized testing and corrected-source checkpoint

The owner authorized f3fbf77 / exposure c7fad27da4122a52b07efb3fd1efa6fcbfbb2c3f884f24b0c7c9257853626e90.
Actual results: privacy contracts 22 pass, frontend client 11 pass, auth/conversation/
logging unit 49 pass; privacy PG 14 pass/13 fail and existing integration 49 pass/2 fail.
Test fixture corrections did not change exposure. Two source corrections are now
prepared: remove redundant conversation child locking without granting more rights;
separate users-only OLD.status access in the shared DB trigger. Corrected exposure
13e5dbf0a8e35918ef4c61d4787f544d08c0c3459d382cc3a4825b9876c688c1
has NOT executed. Stop for fresh explicit synthetic runtime authorization before
running corrected app/migrations/tests. A 100-parent/500-message capacity case is
prepared, not run; the 24h capacity/recovery bound is unproven. No security acceptance
records, inventory/baseline, snapshots or expiry changed; no push/PR. Human CRITICAL
review remains unconfirmed. See docs/P2_05_EXPOSURE_ASSESSMENT.md and its sanitized
runtime evidence. Existing unrelated passing evidence should be reused where valid.

## P2-05 second authorized validation and column-projection checkpoint

Owner authorization covered 095aa659 / 13e5dbf0a8e35918ef4c61d4787f544d08c0c3459d382cc3a4825b9876c688c1.
Actual results: privacy PG 25 pass/3 fail; targeted regressions 14/14 pass. Capacity
100 conversations/500 messages passed in 0.204737771 seconds for the maintenance call;
catch-up/backlog/concurrency passed. This is bounded synthetic evidence, not a deadline
guarantee. Temporary systemd unit verification passed; no timer was installed.
Remaining account-completion failures require SELECT of one authorized column rather
than EXISTS SELECT *. Correction source 50f4724 and stronger rollback assertion a21cb89
are prepared, NOT executed. New exposure e363174d230cc0732e221d1bae835b0bc95bb6cc0921ef029c34b7a589ea797d
requires fresh explicit runtime authorization before corrected app/tests/migrations
execute. Rebuild/scans may inspect packaging without executing the app. No grants,
security acceptance, expiry, baseline/inventory or historical snapshots changed.
No push/PR. Human CRITICAL review remains unconfirmed. Reuse unaffected passing evidence.
