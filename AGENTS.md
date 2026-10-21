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

## Current scope — P3-03A source remediation; runtime authorization pending

The owner authorizes issue #36 on feat/p3-03a-model-quality-remediation: compact
versioned bilingual prompts, server-owned unverified-county abstention, completion
status/timing and honest evaluation metrics with offline tests. No P3-04, generation
API, frontend generation, RAG or new live-model grant. PR #35 is merged; source changes
are not covered automatically by its exact-exposure acceptance.

Before executing changed application code, report exact commit/exposure and fresh
scan/dependency delta; stop for explicit isolated synthetic runtime authorization.
Static validation and packaging-only scans may prepare that checkpoint. No security
acceptance/baseline/inventory/snapshot edit, push or PR until the required separate
decisions. Preserve seven checks, full scans, branch protection, domain privacy and
logging controls. Never treat policy fallback responses as Llama quality evidence.
Expiry stays 23 October 2026, 23:59 EAT. No real data or public/production deployment.
Only the 19 October actual human CRITICAL review is confirmed; 20 October review is
not confirmed. No invented future reviews, automatic renewal or merge. Earlier
approval statements below remain historical and exact-exposure scoped.

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

## P2-05 final functional evidence; security-record decision pending

The owner authorized bd6dd2b / e363174d230cc0732e221d1bae835b0bc95bb6cc0921ef029c34b7a589ea797d.
The three account-completion cases and strengthened audit rollback now passed 4/4;
no new source correction was needed. All 28 privacy cases have passing provenance
(24 unaffected retained +4 reruns), not a claim of another full 28-case run. Reuse
14 targeted regressions, 22 contracts, 49 unit and 11 frontend results where valid.
Final image scans have this same exposure and exact unchanged inventories/findings:
115 HIGH/3 CRITICAL, no reported fixes/KEV matches. Human review is still unconfirmed.
The exact five-file P2-05 acceptance/snapshot/docs update is only PROPOSED in the
exposure assessment, not approved or applied. No push/PR until that explicit approval;
no merge, expiry extension, production/real data, or automatic future acceptance.
The optional bounded iterative-testing clause is also a PROPOSAL ONLY. It is not an
implemented exception; retain exact-hash CI enforcement and current runtime gates.


## Owner-approved P2-05 exact security-record decision

The owner explicitly approved reviewed commit aa2f491a9899e2a6bc712feb28c993911e3d2743
and tested exposure e363174d230cc0732e221d1bae835b0bc95bb6cc0921ef029c34b7a589ea797d
in PHASE 2 FINALIZE P2-05 AND ACCELERATE P2-06. This supersedes earlier pending
record-decision statements for this exact exposure only. The active decision binds
all 118 unchanged individually enumerated OS occurrences: 115 HIGH/3 CRITICAL.
Previous P2-04 approval bytes are preserved at
docs/security/p2-05/p2-04-acceptance-snapshot.json (SHA-256
70a67aaac3b95c86782534965cc1078fc7b24d7e6f45f6a28e6fcb24da90bc6e).
No baseline, inventory-policy or finding suppression changed. Evidence is consolidated
in docs/P2_05_EXPOSURE_ASSESSMENT.md and docs/security/p2-05/final-validation-summary.json.

Only isolated synthetic development through 23 October 2026, 23:59 EAT is accepted.
All fix/new-finding/severity/KEV/exposure/dependency invalidation triggers, complete
scans, seven mandatory checks and branch protection remain enforced. No real data,
production credentials/deployment, automatic renewal, future-exposure approval or
merge. Daily actual human CRITICAL review remains required and unconfirmed. This
owner decision does not record review completion.

The proposed bounded iterative-testing clause is NOT approved or implemented.
Current runtime authorization rules remain unchanged; any proposal must be considered
separately. Publish P2-05 through its feature-branch PR linked to #21 and normal CI.
Prepare P2-06 separately; final acceptance PR/validation follows reviewed P2-05 merge.
No automatic Phase 2 closure, P2-06 merge or Phase 3 implementation is authorized.

## P2-06 final verification — 19 October 2026

PR #28 is merged at 75f5006130b1e5e72cf9f9602e2eab4e5419af42. P2-06 is
documentation/evidence only; see docs/PHASE_2_ACCEPTANCE.md. On 19 October the owner
explicitly confirmed personal review of all three existing CRITICAL assessments:
“I reviewed all three today; continue restricted acceptance”. This supersedes earlier
unconfirmed status for that date only. Future daily reviews remain required.
No acceptance/baseline/inventory record or authorization rule changes. Preserve the
23 October 2026 23:59 EAT expiry, synthetic-only scope and production prohibition.
No automatic merge, formal closure or Phase 3 implementation.

## Owner-approved P3-01 security decision

The owner explicitly approved f53e4aa6f904c8640d12cdca59ef177044ef498b and tested
exposure 54a7c2e7d075593f17107dd652edf035b28b7a399611f700c095bc5f1b04ecc4.
This supersedes prior pending P3-01 acceptance/publication statements for that exact
exposure only. 43 provider and 128 backend regressions passed; inventories unchanged,
115 HIGH/3 CRITICAL remain individually tracked, no reported fixes/KEV matches.
Previous Phase 2 acceptance is preserved byte-for-byte in
`docs/security/p3-01/p2-05-acceptance-snapshot.json` (SHA-256
d7e62ed76852a7646cc6cdf5908bad210b33ea2cc989521007988b8aade46c3e).
Only synthetic isolated local development through 23 October 2026, 23:59 EAT.
Daily actual human CRITICAL reviews and all existing invalidation triggers remain
mandatory; the dated 19 October confirmation is not a future daily review.
No live inference, real data, production deployment, automatic renewal or future
exposure approval. Preserve all seven checks, scanning, exact inventories, historical
records and branch protection. Publish the P3-01 branch/PR linked to #30 and run
normal hosted CI. No automatic merge or P3-02 implementation before reviewed merge.

## Owner-approved P3-02 exact security/inventory decision

The owner approved 9b399b7be1cf76f98bdb24f502dbea876e7f54eb and tested exposure
8e1fa66f0928b01552045590813ad04f971c29a3c443dd92358721ccdc27a41d under the exact
seven-file proposal in docs/P3_02_EXPOSURE_ASSESSMENT.md. This supersedes pending
P3-02 record/publication statements for that exact exposure only. Backend inventory
is 122 packages: httpx 0.28.1, httpcore 1.0.9 and certifi 2026.7.22 are promoted from
existing locked development packages. Only backend report provenance/inventory and
active acceptance binding change; all 115 HIGH/3 CRITICAL occurrence rows, severities,
pins and other inventories remain unchanged. Prior P3-01 policy bytes are preserved
in docs/security/p3-02/p3-01-policy-snapshot.json with exact reconstruction hashes.

68 mocked Ollama, 43 provider and 128 backend regression tests passed. Publication
and seven normal hosted checks are authorized; no automatic merge. Acceptance stays
synthetic/local only through 23 October 2026, 23:59 EAT. Preserve all invalidation
triggers, actual daily human CRITICAL reviews, complete scans, seven checks and branch
protection. The existing dated 19 October human review is not a future-day review.
No privilege/network expansion, model install/download, live inference, real data,
production deployment, expiry extension or automatic future-exposure acceptance.

## Owner-approved P3-03 security/publication decision

The owner explicitly approved reviewed commit
572485e275252508f0b9d50dba05d1424030d36f and tested exposure
95a4fcbaa568938334a96ba19eb10f868802c7f6ba26dfd20d4363b850b8bf00.
This supersedes pending P3-03 publication statements for that exact exposure only.
Previous P3-02 acceptance is preserved byte-for-byte in
`docs/security/p3-03/p3-02-acceptance-snapshot.json`
(SHA-256 c9bd2f9cdcb78e6b3e19476db8c06c5a7ea7e0e6ef4196326a477521d17b3063).
All 115 HIGH/3 CRITICAL occurrences, base-image pins and dependency inventories remain
unchanged. No baseline/inventory-policy update, finding suppression or control change.

38 orchestration, 111 provider/Ollama and 128 backend regressions passed. The 100-case
fake evaluation has 50/50 length compliance per language; zero claim flags does not
prove factuality. Uncertainty signals are 0/36 per language because the unchanged
fake provider returns fixed text. This measures fake response content, not semantic
enforcement by orchestration: tests verify that the orchestrator sends the right
instructions and bounds, but it does not enforce semantic abstention. Missing
validation is separately authorized real-model evaluation and independent bilingual
review against those instructions. Injection resistance and live Llama quality are
not established. Do not present the model as safe for official county guidance.

Acceptance remains isolated synthetic development only through 23 October 2026,
23:59 EAT. All fix/new-finding/severity/KEV/exposure/dependency invalidation rules,
actual daily human CRITICAL reviews, full scans, seven required checks, branch
protection and normal PR review remain enforced. The dated 19 October review is not
a future daily review. No expiry renewal, future-exposure authorization, public or
production deployment, real citizen data, live inference or model downloads.
Publish the branch/PR linked to #34 and run normal hosted CI. No automatic merge.

## Owner-approved P3-03A exact security/publication decision

The owner explicitly approved reviewed commit
bd8b0d848b5ac36dd513f9f4535e728c75e61e46 and tested exposure
dc3e34e2151091e03e21d1929f28a6d6e0b0e0208604663dabef98b55d623780.
This supersedes pending P3-03A runtime/record/publication statements for this exact
exposure only. The owner personally confirmed review of SQLite CVE-2025-7458,
libxml2 CVE-2026-6653 and zlib1g CVE-2023-45853 assessments dated 20 October 2026:
“I have personally reviewed the three CRITICAL findings”. Confirmation was recorded
at 2026-10-20T16:29:11.959671+00:00; this is not a claim about the minute the review was performed.
Future daily actual reviews remain required; no future review is inferred.

Previous P3-03 acceptance is preserved byte-for-byte at
`docs/security/p3-03a/p3-03-acceptance-snapshot.json` (SHA-256
9aae9dd0b4ebb7bcafc07206d4042611f49c3076d558dfccca6c2c9571f6a016).
All 115 HIGH/3 CRITICAL finding rows, inventories, image pins, seven checks, full
scanning, branch protection and invalidation triggers remain unchanged. No baseline
or inventory-policy change, suppression or automatic future acceptance.

313 tests passed: 36 remediation, 149 orchestration/provider, 128 regressions.
Policy uncertainty signals were 36/36 per language; fake signals 0/36 and suspected
incomplete fake markers 50/50 per language. No Llama inference occurred during this
validation. Policy responses are not successful model answers; live accuracy and
latency improvement remain unproven.

Acceptance stays isolated synthetic development only through 23 October 2026,
23:59 EAT. No real citizen/county data, public/production deployment, public Ollama,
live inference, model downloads, renewal, future exposure authorization or automatic
merge. The exact five-file decision and publication are now approved; publish the
branch/PR linked to #36 through all seven normal hosted checks.

## Owner-approved P3-03B scoped exposure decision

The owner explicitly authorized validated commit 9594dc339bd93939113817a6ba0a132ecc062ea3
and exposure d015b5cadfa07781d0f2eb063bb11bbd7dea923a684bad94a78dbae3506f476d
for isolated synthetic development and the conditional 96-scored/six-warm-up
Llama/Qwen benchmark. See docs/P3_03B_EXPOSURE_ASSESSMENT.md (repository-relative).
P3-03A approval bytes preserved in docs/security/p3-03b/p3-03a-acceptance-snapshot.json
(SHA-256 9619c830542bb5495256e338b8c57d82ef5536b2d8bf6a3bba81928952545211). No baseline/inventory/control changes.
115 HIGH/3 CRITICAL remain. Actual 20 October human review is confirmed; future
daily reviews are not inferred. Expiry remains 23 October 2026, 23:59 EAT; all
invalidation rules, scanning, seven checks and branch protection remain enforced.
Require runtime resource and isolation prerequisites. No production/real data/public
Ollama, additional models, automatic selection, publication, merge or P3-04.

## Owner-approved certifi-only security-record decision

Exact exposure 8fb62f79a81d7d1216126f0b4ff40fb38a9e3d01b625646b121bcb83e5b00c9f
and backend inventory f508af45849f6d64bbf4f6cc65b4cd411e22da300492f630f479cc64f1be3de4
are explicitly owner-approved for validated commit b585728899466618f28c6f34104a0ff5deb5a825. The new certifi
2026.10.19 locks resolve GHSA-6q48-6c7w-9gw2; no unrelated package changes. Prior
policy bytes are preserved byte-for-byte in docs/security/pr-40-certifi/p3-03b-policy-snapshot.json.
All inherited 115 HIGH/3 CRITICAL findings and expiry 23 October 2026 23:59 EAT remain.
No future human review is inferred from 20 October confirmation. Preserve all
controls/invalidation, synthetic-only scope and production ban. No automatic
merge, new model inference, P3-04 readiness or acceptance renewal.

The owner authorizes pushing this branch to existing PR #40 and running all seven
normal hosted checks. This supersedes earlier pending publication statements only
for this exact remediation. No authorization requirement is weakened or bypassed.

## Owner-approved P3-03D exact-exposure security/publication decision

Explicit owner approval of the exact five-file proposal for tested source
bb1f88d4896d3f579fd21a441629190db7d19d4d and unchanged exposure
015755bffa0f038986d719624979b317cb5e5527dceed76447fd207d09747ab1.
See docs/P3_03D_EXPOSURE_ASSESSMENT.md. Runtime 115 HIGH/3 CRITICAL and complete
inventories remain unchanged; builder residual 56 HIGH/1 CRITICAL is separately
disclosed, including duplicate zlib CVE. Preserve PR #40 approval bytes in
docs/security/p3-03d/pr-40-acceptance-snapshot.json. No 21 October human review is
inferred; actual daily confirmation remains required. Keep all invalidation rules,
seven checks, full scans and branch protection. Expiry stays 23 October 2026,
23:59 EAT. The owner explicitly authorizes
only this reviewed exposure and normal branch publication/CI; never bypass
future exposure/runtime authorization. No renewal, production, real data, public
Ollama, inference or automatic merge.

## Owner-approved restricted-development renewal — 21 October 2026

Owner approved the exact five-file proposal for merged commit
2fc0ecfd895739eef3f026c2961c286c0a1397a8 and unchanged exposure
015755bffa0f038986d719624979b317cb5e5527dceed76447fd207d09747ab1.
The owner explicitly confirmed: “I personally completed this review on 21 October
and acknowledge the residual risks”, covering SQLite, libxml2 and zlib in both
PostgreSQL and the Node builder. This records the date actually confirmed, not the
minute review was performed; future daily reviews remain due and are not inferred.
See docs/SECURITY_RENEWAL_2026_10_21.md. Preserve the previous approval bytes in
docs/security/renewal-2026-10-21/p3-03d-acceptance-snapshot.json. Runtime 115 HIGH/
3 CRITICAL and separately disclosed builder 56 HIGH/1 CRITICAL remain tracked.
New end is 30 October 2026, 23:59 EAT, effective only after this renewal PR is
reviewed/merged and repository-policy conditions pass. Until then main's existing
23 October expiry remains authoritative. The owner authorizes this focused branch,
PR and all seven normal hosted checks; no automatic merge. Keep daily actual
CRITICAL reviews, daily scans, all invalidation rules, seven app-bound checks,
strict protected PRs and least privilege. No future-exposure/runtime authorization,
live inference, new models, public Ollama, real data, production or automatic future
renewal is granted. Issue #39 and P3-04 readiness remain unresolved independently.
