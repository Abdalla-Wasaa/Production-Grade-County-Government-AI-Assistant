# Phase 2 acceptance candidate

Status: **not accepted**. P2-05 [PR #28](https://github.com/Abdalla-Wasaa/Production-Grade-County-Government-AI-Assistant/pull/28)
has all seven required checks passing at head 1302d9826daaf4c204f1724a8a15662eeda34ff9
and is awaiting owner review/merge. This document is prepared on
`docs/p2-06-acceptance` from main, separately from P2-05. Final clean-checkout and
operational verification must follow reviewed P2-05 merge; no acceptance PR is open.

Scope is the existing [roadmap](ROADMAP.md) Phase 2: invite-only identity, private
ordered conversations, bilingual history and tested privacy retention. No public
registration, provider dispatch, real data, production approval or automatic Phase 3.
The CLOSED state of trackers #21/#22 does not establish that their unchecked exit
criteria have passed. Record actual evidence and obtain the owner's closure decision.

## Existing evidence to retain

| Existing exit criterion | Verified evidence and reuse | Remaining final verification |
| --- | --- | --- |
| Identity/API contracts and access controls | [Authentication](AUTHENTICATION.md), [operations](AUTHENTICATION_OPERATIONS.md), [P2-01](P2_01_EXPOSURE_ASSESSMENT.md), [P2-02](P2_02_EXPOSURE_ASSESSMENT.md); current P2-05 targeted auth/ownership/revocation/outage regressions 14/14 | Clean-checkout synthetic provisioning/activation/session verification; match final merged source; no public signup |
| Ordered private history and safe mutations | [P2-03](P2_03_EXPOSURE_ASSESSMENT.md), [P2-04](P2_04_EXPOSURE_ASSESSMENT.md); existing ownership/concurrency/CSRF/history cases and browser/axe evidence | Reuse unaffected reports with source provenance; verify final onboarding flow and record manual language/accessibility status honestly |
| Privacy retention, holds and deletion | P2-05 final-validation-summary.json maps all 28 privacy cases to passing provenance; 24 unaffected retained plus four final reruns; strict injected audit rollback passed | P2-05 reviewed merge; clean-checkout operator/maintenance runbook replay and final permissions verification |
| Migration and cascade integrity | P2-05 migration 0006 pristine upgrade/downgrade, retained-hold downgrade rejection, account deletion and message/session cascade tests | Fresh-checkout explicit upgrade/check/readiness to 0006; no forced downgrade through retained controls |
| Bounded daily maintenance and recovery | 100 conversations/500 messages purged in 0.204737771 seconds; catch-up/backlog/concurrency passed; temporary systemd user-unit verification passed | Verify operator commands and chosen runner operationally; record scheduler installation/run status; preserve documented capacity/availability assumptions |
| Seven protected CI checks | Existing pinned workflows and ruleset 25222082; no controls changed by P2-05 | All seven latest-head contexts pass, sanitized artifacts downloadable, required checks/app binding and protection still enforced |
| Restricted development security | P2-05 approved exposure e363174d230cc0732e221d1bae835b0bc95bb6cc0921ef029c34b7a589ea797d; fresh scans 115 HIGH/3 CRITICAL, exact inventories unchanged, no reported fixes/KEV matches | Verify active decision and byte-preserved P2-04 snapshot; current scans/audits/secret checks; actual daily human review status |

P2-05 evidence paths, available after that merge:
`docs/P2_05_EXPOSURE_ASSESSMENT.md`, `docs/PRIVACY_LIFECYCLE.md`,
`docs/security/p2-05/final-validation-summary.json`, `final-scan-summary.json`,
`final-image-manifest.json` and the linked sanitized JUnit reports. Do not relabel
retained results as a new full-suite execution. Explicitly supersede any historical
failure only with the matching corrected test/source evidence.

## Clean-checkout reproduction instructions — not executed yet

Use an approved Linux host/daemon, synthetic records and an exact merged candidate.
Ordinary `county-dev` onboarding needs a genuinely isolated Docker daemon/host with
its own socket/data root and no existing state. A different checkout or project name
on the shared daemon is not equivalent. The Phase 1 isolated-daemon procedure in
[existing acceptance](PHASE_1_ACCEPTANCE.md) can be reused; never stop/prune coursework
containers. If the daemon cannot start, report the affected evidence unavailable.

After P2-05 is merged, make an ordinary clean clone of the official repository and
record the exact SHA, initial `git status --porcelain`, tool versions, daemon identity
and empty initial container/volume state. Explicitly select the isolated Docker socket
through `DOCKER_HOST`. Never copy old `.env`, secret files or PostgreSQL volumes.

From the new checkout, following [Compose development](COMPOSE_DEVELOPMENT.md):

```bash
python3 scripts/dev.py setup
python3 scripts/dev.py setup
docker compose config --quiet
docker compose build
docker compose up -d
docker compose ps
curl -i http://127.0.0.1:8080/proxy-health
curl -i http://127.0.0.1:8080/health/live
curl -i http://127.0.0.1:8080/health/ready
docker compose --profile maintenance run --rm migrate upgrade
docker compose --profile maintenance run --rm migrate check
curl -i http://127.0.0.1:8080/health/ready
```

Expect setup reuse without overwriting credentials, proxy/live 200, ready 503 before
explicit migration and 200 only with reachable current schema. Ordinary Compose
still defaults to auth disabled; do not imply that health-only startup proves
bilingual authentication/history. Use the existing synthetic authenticated smoke
harness and documented host/operator setup for those paths; do not introduce raw
secret environment values into Compose configuration or credentials in argv/logs.

For reproducible locked tooling, use the existing commands in
[Contributing](../CONTRIBUTING.md) and Phase 1 acceptance: Python 3.12, uv/uv.lock,
Node 24/npm lock; hash-verified repository tooling. No lock regeneration or dependency
upgrades. Run only the mandatory replay/checks still needed for this candidate;
retain valid prior suites instead of repeating unrelated tests.

With the approved frontend/browser environment, from the clone root:

```bash
python3 scripts/compose_smoke.py --browser --report .artifacts/compose-images.json --cleanup-manifest .artifacts/compose-cleanup.json --diagnostics .artifacts/compose-diagnostics.json
```

Record actual auth/history/migration/integration/browser outcomes and report counts.
The harness uses owned random projects, not the ordinary county-dev resources. Preserve
immutable runtime IDs for scanning; sanitize reports with the existing report checker.
Use existing audit/scanner/secret commands and seven required checks unchanged.
A missing/all-skipped/malformed/failed report cannot be counted as a passing result.

## Privacy runbook and recovery verification — pending final replay

After migration 0006, provision only dedicated unprivileged operator/maintenance
roles; use the existing explicit grant command with `--privacy-audit-key-file` to
pin the existing auth HMAC key. Follow the merged privacy runbook for file paths,
UUID-only case references, actual operator verification and safe outputs. Do not
reuse the removed legacy purge bypass or grant broad SELECT/UPDATE to clear a test.

Verify synthetic hold create/review/release, held DELETE 409, immediate account
disable/session revocation, idempotent request status/completion, eligible cascade
removal, mandatory audit failure rollback and ledger preservation. Reuse the 28-case
PG evidence where unchanged; record the clean-checkout operator-command proof rather
than rerunning every unrelated case. Confirm actual role privileges, key mismatch
rejection and content/credential-free output. Human verification is never supplied
by an automated fixture outside the synthetic test exercise.

Verify the chosen runner's bounded `tick` command, explicit missed-run catch-up,
nonblocking overlap and visible failure/attention exit codes. Unit templates must
use this checkout's actual paths and private files. Record whether a scheduler was
actually installed/exercised; syntax checks are not evidence of unattended execution.
The existing 02:00 Nairobi daily target uses 15-minute catch-up checks and a 23-hour
urgency threshold under the runbook's availability/capacity assumptions. The measured
100-parent/500-message case is not proof for unbounded cascades or unavailable hosts.
A missed assumption requires an owner capacity/policy decision, not deadline relaxation.

Use controlled dependency stop/start only in the owned isolated stack. Confirm ready
503/live 200 during database outage and recovery to ready 200; confirm persistence
across ordinary shutdown/start. Use existing ownership-checked reset for disposable
cleanup, not global pruning. Backup restore/ledger replay remains an explicit
operational limitation; do not claim production backup or erasure assurance.

## CI, security and honest acceptance record

Required context names are exactly `backend-quality`, `postgresql-integration`,
`python-dependency-audit`, `frontend-quality`, `compose-integration`,
`repository-quality`, `secret-scan`. Verify GitHub Actions app 15368 and ruleset
25222082 on main, strict synchronization, resolved conversations, zero external
approval requirement, blocked force-push/deletion and no bypass actors. Read settings;
do not alter them. Reuse the existing controlled enforcement evidence unless a
configuration change or unresolved concern requires another safe test.

For every final check, record commit, run/job URL, actual conclusion and artifact
integrity. Fresh final image findings/inventories must match the exact active owner
decision; no new fixable, KEV-listed, escalated or newly discovered finding is
implicitly accepted. Production stays prohibited, with no real county/citizen data.
The existing expiry is 23 October 2026, 23:59 EAT; no extension or automatic renewal.
Daily actual human review of the three CRITICAL findings remains **unconfirmed**.
Record actual dated evidence only when provided, not an agent claim or CI result.

Manual fluent Kiswahili and screen-reader review status must also be explicit.
Automated bilingual tests/axe are evidence, not language or WCAG certification.
Keep legal/pilot/privacy/provider approval gates intact. P2-06 documentation does not
change application exposure policy, accept new findings or authorize production.

## Remaining acceptance gates and decision

- P2-05 latest-head CI: seven passed; owner-reviewed merge remains pending.
- Clean isolated-checkout onboarding/migration/operator/runner/recovery replay: pending.
- Final seven-check/artifact/security/ruleset verification: pending.
- Actual human CRITICAL-review evidence: unconfirmed; no fabricated completion.
- Manual language/accessibility status and operational limitations: record honestly.
- Separate P2-06 PR and explicit restricted-development closure decision: pending.

Only after actual criteria are satisfied should this candidate become an acceptance
report. Do not infer closure from a tracker status or automatically merge either PR.
After separate Phase 3 approval, the first implementation task is the AI provider
interface and OpenAI adapter with mocked contracts and bounded timeout/error handling;
no live-provider calls or conversation-generation endpoint is approved by this report.


## Verified P2-05 hosted handover

PR #28 head `1302d9826daaf4c204f1724a8a15662eeda34ff9` has all seven SUCCESS check
runs bound to GitHub Actions app 15368; GitHub reports CLEAN / MERGEABLE and zero
unresolved review threads. These are P2-05 results, not P2-06 final acceptance.

| Context | Run evidence | Result |
| --- | --- | --- |
| backend-quality | [Backend run](https://github.com/Abdalla-Wasaa/Production-Grade-County-Government-AI-Assistant/actions/runs/39242616707) | SUCCESS; 128 unit cases |
| postgresql-integration | Same backend run; postgresql-results artifact | SUCCESS; 79 PG cases including all 28 privacy cases |
| python-dependency-audit | Same backend run; python-dependency-reports artifact | SUCCESS |
| frontend-quality | [Frontend run](https://github.com/Abdalla-Wasaa/Production-Grade-County-Government-AI-Assistant/actions/runs/39242616684) | SUCCESS; 88 unit and 87 browser cases |
| repository-quality | [Repository run](https://github.com/Abdalla-Wasaa/Production-Grade-County-Government-AI-Assistant/actions/runs/39242616731) | SUCCESS; 41 tooling cases |
| secret-scan | Same repository run | SUCCESS |
| compose-integration | [Compose run](https://github.com/Abdalla-Wasaa/Production-Grade-County-Government-AI-Assistant/actions/runs/39242616660) | SUCCESS; both retained browser reports pass, complete image policy passes |

Artifacts from all four runs were downloaded and their JUnit reports validated.
Compose image decision has zero policy failures: backend 44 HIGH, PostgreSQL
71 HIGH/3 CRITICAL, web zero. No findings were removed from the baseline and no
security control was bypassed. Current exact exposure is
`e363174d230cc0732e221d1bae835b0bc95bb6cc0921ef029c34b7a589ea797d`.

The approved five-file decision preserves prior P2-04 bytes at
`docs/security/p2-05/p2-04-acceptance-snapshot.json`, SHA-256
`70a67aaac3b95c86782534965cc1078fc7b24d7e6f45f6a28e6fcb24da90bc6e`.
Expiry, all invalidation rules, isolated synthetic scope and production prohibition
remain unchanged. No bounded-testing policy amendment was implemented. Actual daily
human CRITICAL review remains unconfirmed. Do not relabel these CI results as that
review, a clean-checkout operational replay or formal Phase 2 acceptance.

The P2-06 documentation candidate was statically checked in a separate independent
validation clone because the current repository checker deliberately rejects linked
worktrees. That document-only check is not the final runtime reproduction. After
reviewed P2-05 merge, incorporate main without rewriting published history, perform
only the remaining mandatory final checks above, then open the separate P2-06 PR.
