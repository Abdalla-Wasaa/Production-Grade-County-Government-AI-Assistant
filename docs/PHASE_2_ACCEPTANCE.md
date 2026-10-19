# Phase 2 final verification and restricted-development acceptance candidate

Status: **technical verification passed; owner review/merge and formal closure pending**.
P2-05 [PR #28](https://github.com/Abdalla-Wasaa/Production-Grade-County-Government-AI-Assistant/pull/28)
was merged on 19 October 2026 at 11:22:11 UTC, commit
`75f5006130b1e5e72cf9f9602e2eab4e5419af42`. All seven checks passed on both its
reviewed head and merged main. This separate `docs/p2-06-acceptance` branch includes
that main without rewriting history. No application, workflow or acceptance-policy
code changes are part of this milestone.

## Roadmap exit criteria and evidence

The existing [roadmap](ROADMAP.md) defines Phase 2 as invite-only identity,
private ordered conversations, bilingual history and tested privacy retention.
[Issue #22](https://github.com/Abdalla-Wasaa/Production-Grade-County-Government-AI-Assistant/issues/22)
tracker state alone is not acceptance. The following maps its actual exit criteria.

| Criterion | Automated and retained evidence | Final clean-checkout replay |
| --- | --- | --- |
| API contracts, roles and ownership | [Authentication](AUTHENTICATION.md), ADR 0002, P2-01/02 assessments; merged-main backend 128 unit and 79 PostgreSQL cases, including unauthorized/cross-user rejection | Synthetic invitation CLI, activation/login, current user, CSRF/refresh/session revocation and bilingual browser flow passed |
| Ordered private conversations | [P2-03](P2_03_EXPOSURE_ASSESSMENT.md), [P2-04](P2_04_EXPOSURE_ASSESSMENT.md); concurrency/idempotency/ownership/history cases, 88 frontend unit and 87 browser cases in hosted evidence | Creation/history/message persistence/rename/delete and session restoration passed through Nginx and real backend |
| Cascades, holds and retention | [P2-05](P2_05_EXPOSURE_ASSESSMENT.md); all 28 privacy PG cases pass in hosted 79-case suite, rollback/concurrency/catch-up retained | Operator hold create/review/release, held DELETE 409, immediate access revocation, account/message cascade, ledger and idempotent completion passed |
| Explicit migrations and least privilege | Existing migration upgrade/downgrade and held-record downgrade-rejection tests | Fresh explicit upgrade/check through `0006_privacy_lifecycle`; ready 503 before migration then 200; runtime DDL/revision-write denial and dedicated restricted operator/maintenance grants verified |
| Retention job and recovery | 30-day inactivity/90-day maximum contract; bounded purge/catch-up tests; measured 100 conversations/500 messages in 0.204737771 seconds | CLI failure/recovery and actual hardened service, timer dispatch, dependency-failure alert and recovery passed |
| Protected workflow/security | Seven merged-main contexts SUCCESS; complete scans/audits/secret checks; ruleset 25222082 active | Independent fresh image scans pass unchanged policy; exact exposure/inventories retained; actual owner CRITICAL review confirmed 19 October |

Existing P2-01 through P2-05 assessments and
[final P2-05 evidence](security/p2-05/final-validation-summary.json) retain exact
source/test provenance. They are reused, not relabelled as new full local-suite runs.
No provider dispatch, public registration, fabricated AI responses or production
approval is introduced.

## Clean-checkout reproduction and operational results

A new clone from the official GitHub origin at the merge above started with clean
tracked files, no copied configuration and a separate empty Docker daemon (no images,
containers or volumes). [Initial proof](security/p2-06/clean-start.json) records the
commit and daemon identity. Locked `uv sync --locked` with Python 3.12.3 and `npm ci`
with Node 24.22.0 succeeded; dependencies were not regenerated.

Following [Compose development](COMPOSE_DEVELOPMENT.md), executed:

```bash
python3 scripts/dev.py setup
python3 scripts/dev.py setup
docker compose config --quiet
docker compose build
docker compose up -d
docker compose --profile maintenance run --rm -T migrate upgrade
docker compose --profile maintenance run --rm -T migrate check
```

Fresh vendor-pinned builds, safe setup reuse, Nginx SPA/API routing, non-root/read-only
containers, internal database networking and mounted secret-file configuration passed.
`/proxy-health` and `/health/live` returned 200; readiness returned safe 503 before
migration or during DB outage and 200 after current-schema/reachable-DB recovery.
Shutdown/restart retained data and revocations. The existing synthetic authenticated
browser harness was exercised against this ordinary `county-dev` stack, including
English/Kiswahili history. Its single browser case passed; this is additional final
onboarding evidence, not a claim to rerun all 87 hosted browser cases locally.

The [operational proof](security/p2-06/clean-checkout-operations.json) records actual
stages. Identity/privileged maintenance commands followed
[authentication operations](AUTHENTICATION_OPERATIONS.md) and
[privacy lifecycle](PRIVACY_LIFECYCLE.md): private URL/key files, existing HMAC pin,
dedicated restricted roles, synthetic UUID case references and safe outputs.
Hold/revocation/deletion and ledger checks passed without broadening database grants.
The clone's tracked tree remained clean after verification.

### Scheduler and recovery

[Runner evidence](security/p2-06/runner-verification.json) records actual service
execution, timer dispatch, visible PostgreSQL-outage failure/OnFailure alert and
successful recovery. Temporary owned units used the shipped protections unchanged,
with checkout/env paths substituted, a read-only bind for the temporary checkout and
the isolated network namespace. A test-only two-second timer trigger supplemented
the original calendar to verify dispatch without waiting until 02:00. This does not
claim observation of an overnight deadline or permanent scheduler installation.

The user-level systemd manager could not join the isolated network namespace; its
initial harness run failed safely. The corrected disposable harness used system-level
runtime units, preserving sandbox controls; all four stages passed. All owned units
were removed. Operators must install and monitor their chosen supported runner in
their own environment; unattended production operation is not established here.

Existing bounded batches/locking/catch-up and injected audit-rollback tests are
retained. The small purge benchmark supports only its documented workload and host
conditions. The 24-hour target depends on scheduling, monitoring, availability and
capacity assumptions; it is not a guarantee under arbitrary load or host outage.
Backup restoration with deletion-ledger replay, production RPO/RTO and real erasure
assurance remain later operational gates.

## Hosted CI and branch protection

[Exact merged-main checks](security/p2-06/merged-main-checks.json) record seven
SUCCESS contexts from GitHub Actions app 15368:

| Required context | Merged-main run |
| --- | --- |
| backend-quality | [Backend](https://github.com/Abdalla-Wasaa/Production-Grade-County-Government-AI-Assistant/actions/runs/39244135443) |
| postgresql-integration | Same backend run |
| python-dependency-audit | Same backend run |
| frontend-quality | [Frontend](https://github.com/Abdalla-Wasaa/Production-Grade-County-Government-AI-Assistant/actions/runs/39244135473) |
| repository-quality | [Repository](https://github.com/Abdalla-Wasaa/Production-Grade-County-Government-AI-Assistant/actions/runs/39244135341) |
| secret-scan | Same repository run |
| compose-integration | [Compose](https://github.com/Abdalla-Wasaa/Production-Grade-County-Government-AI-Assistant/actions/runs/39244135391) |

Downloaded P2-05 hosted artifacts validate 128 backend unit, 79 PostgreSQL, 88 frontend
unit, 87 browser and 41 tooling cases (including policy negative checks), plus both
Compose browser reports. The fresh merged-main Compose artifacts were downloaded;
complete scan decision has no policy failures. Required final P2-06 PR checks must
also pass before review/merge; use GitHub's latest-head results rather than this table
as a claim about a future PR commit.

Ruleset 25222082 was read back unchanged: active on default main, all seven contexts
bound to app 15368, strict synchronization, resolved conversations, zero mandatory
external approvals, blocked deletion/force pushes and no bypass actors. Controlled
merge-blocking evidence from PR #15 is retained; no settings changed or bypass used.

## Security decision and human review

Application exposure remains
`e363174d230cc0732e221d1bae835b0bc95bb6cc0921ef029c34b7a589ea797d`.
[Fresh local image decision](security/p2-06/image-scan-decision.json), scanned
19 October 2026 11:32 UTC, matches the complete accepted inventories:

| Image | HIGH | CRITICAL | Inventory SHA-256 |
| --- | --- | --- | --- |
| Backend | 44 | 0 | 7c9d236e62e9b96b9dfe7ca03dd92b1d999c6bacfb7fb8f67949a9790d88274e |
| PostgreSQL | 71 | 3 | f0ff6951e8f3157a9f0e6d15387c68b6e4e591afd21d2d0da972c122ed1ad288 |
| Web | 0 | 0 | e9d19af8839b51cd311f6b527994b6cc624ee2b0491513c293f6fefa6cb60443 |

Total **115 HIGH/3 CRITICAL**, no reported fixes or KEV matches in the retrieved
snapshot; these scanner facts are not proof of vulnerability-free code.
[Image manifest](security/p2-06/image-manifest.json) binds immutable runtime image IDs.
CVE-2026-77214 remains absent from the remediated web image.

The owner explicitly confirmed on **19 October 2026**: “I reviewed all three today;
continue restricted acceptance”. [Dated review evidence](security/p2-06/human-critical-review.json)
records CVE-2025-7458 (SQLite crafted SQL prerequisite), CVE-2026-6653 (libxml2,
authenticated SQL/XML plausible path) and CVE-2023-45853 (zlib MiniZip excluded per
Debian assessment, scanner finding retained). See [register](VULNERABILITY_REGISTER.md)
for the individual assessments. This supersedes older pending-review statements for
that date only; future daily human reviews are not completed by this record.

Active acceptance, baseline and inventory policy records remain unchanged. The P2-04
snapshot SHA-256 remains
`70a67aaac3b95c86782534965cc1078fc7b24d7e6f45f6a28e6fcb24da90bc6e`.
Acceptance expires **23 October 2026, 23:59 EAT**; no automatic renewal/expansion.
All fix/new-finding/escalation/KEV/exposure/dependency invalidation rules, scanning,
seven checks and branch protections remain active. No bounded-testing policy exception
was introduced. Only isolated synthetic local development is accepted: no real
citizen/county data, production credentials, public or production deployment.

## Manual limitations and closure decision

Automated bilingual/browser/axe evidence is passing. Independent fluent Kiswahili
and manual screen-reader/WCAG 2.2 AA assessment have **not** been completed; do not
claim accessibility certification or pilot language approval. Those, county/pilot/
legal/provider approvals and production backup/restore/security gates remain explicit
limitations and later release gates.

This report supports restricted-development technical acceptance only. The separate
P2-06 PR still requires all seven final checks and owner review/merge/closure decision.
No automatic tracker closure, merge, production security approval or Phase 3 start.
The [Phase 3 plan](PHASE_3_PLAN.md) proposes the provider interface and deterministic
fake with mocked contract tests first, then an OpenAI adapter. Separate authorization
is required; no live provider calls or application changes have begun.

## Newly observed scheduled-monitor follow-up

[Scheduled monitor run](https://github.com/Abdalla-Wasaa/Production-Grade-County-Government-AI-Assistant/actions/runs/39245723445)
completed during this audit with 14/15 stages passing. Its single failure is
`registry_1`: the upstream `nginxinc/nginx-unprivileged:stable-alpine-slim` tag now
resolves to `sha256:5d8bb9437d74a600ec5dbf90c035451c724dc33eac8d3a71078f6f8612c345f6`,
while the reviewed runtime remains pinned to
`sha256:4ac59c85c8c46d9e91eaabd2122cda4923ba380cf11f4138e389f069bcdc77a3`.
[Registry evidence](security/p2-06/scheduled-monitor-registry.json) and
[stage results](security/p2-06/scheduled-monitor-status.json) preserve the alert.
All dependency audits, builds and current pinned-image scan-policy stages passed.
This is an upstream tag-change alert, not evidence of a new CVE or a failed scan
of the pinned image. No automatic pin/policy update was made.

Owner disposition of this visible maintenance alert remains a closure follow-up:
review the changed vendor image in a separate scoped update if warranted. The
replacement image has not been assessed or approved here. Do not treat seven green
PR contexts as proof that the separate daily monitor is green.
