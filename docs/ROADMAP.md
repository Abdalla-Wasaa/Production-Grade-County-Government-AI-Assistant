# Milestone roadmap

Status: updated 2026-10-16. Phase 0, P1-01 through P1-04 and security follow-up
PR #12 are merged. P1-05 is authorized and pending review; P1-06 requires separate
approval. Development remains fictional/synthetic only. Estimates assume one focused engineer
with access to a county content reviewer and privacy/security reviewer. Parallel
organizational review is possible; no sub-agent delegation or extra engineering team
is assumed. Part-time work, procurement, credentials, approvals and county source
review can extend elapsed time. Estimates are effort windows, not calendar promises.

[Requirements](REQUIREMENTS.md) defines scope; [architecture](ARCHITECTURE.md),
[database](DATABASE_DESIGN.md), [API](API_SPECIFICATION.md),
[security](SECURITY.md) and [ADR 0001](DECISIONS/0001-modular-monolith.md) define
the proposed implementation baseline. Coursework stays read-only.

## Milestones and acceptance criteria

| Phase / effort estimate | Deliverables | Exit criteria and evidence |
| --- | --- | --- |
| 0: architecture and requirements, merged | Seven linked design documents plus ADR; coursework-informed decisions | Completed through merged PR #1; product features still follow their own milestone gates |
| 1: foundation, 1 week | Isolated frontend/backend packages; locked dependencies; settings; Docker/Compose PostgreSQL; migration framework; CI skeleton; localized UI shell | Fresh clone starts with documented synthetic setup; non-root containers and live/ready behavior verified; frontend build/lint/types and backend smoke/migration checks pass; no live model or citizen data |
| 2: identity and conversations, 2–3 weeks | Invite-only acceptance/provisioning procedure; secure sessions; users/conversations/messages migrations; API and bilingual history UI | API contract tests pass; role/ownership 401/403/404 tests; CSRF/rotation/revocation/concurrency tests; ordered history and cascade deletion verified; privacy notice/retention job tested; no provider dispatch |
| 3: bounded OpenAI assistant MVP, 3–4 weeks | Provider port + OpenAI adapter; reviewed service catalogue; bounded memory; durable attempts/retry/recovery; quota/budget ledger; bilingual replies and source/abstention UI | All FR-01..FR-10 verified for closed pilot; >=100 reviewed held-out cases and per-language gates; failure/deletion/replay tests; 10-user load measurement, token/spend caps and deadline checks; provider/privacy approval before any real-data call |
| 4: secure public document RAG, 3–4 weeks | Source registry; immutable versions; scanned extraction; chunking/embedding adapter; pgvector migrations; exact retrieval baseline and corpus activation | Owner approves every released source; bilingual retrieval Recall@5 target >=0.85 per language on >=50 relevant cases/language; no unauthorized/withdrawn source in adversarial tests; citation/abstention gates retained; rollback and document purge verified; record benchmark denominators |
| 5: controlled read-only tools, 2–3 weeks | Allowlisted directory/status adapters, schemas, server authorization, result validation and audit | Unknown/unauthorized tools and tampered scopes denied; maximum 2 calls/turn and deadlines enforced; offline adapter contracts and approved sandbox checks pass; no payment/permit/record mutation |
| 6: AWS deployment and operational pilot, 2–3 weeks | Reviewed AWS topology/region; managed secrets/DB; protected deployment pipeline; monitors/runbooks; pilot release record | Hosting/transfer/DPIA/identity approvals; real PostgreSQL restore with deletion replay; RPO/RTO demonstration; load/cost evidence; rollback and incident drills; county reviewers sign off residual risks before real users |

Closed-pilot local MVP: approximately 6–8 focused engineering weeks after Phase 0
approval. Phases 1–6 total approximately 13–18 engineering weeks, excluding review
waits and procurement. The cloud milestone is not required to demonstrate a local
synthetic MVP; local success is not evidence of public-production readiness.

Phase 4 recall target is a proposed evaluation gate, not current measured quality.
Adjust corpus scope or retrieval method if evidence fails; never relax privacy or
silently reduce the benchmark denominator to pass. RAG remains disabled until its
own gate; tools remain disabled until their gate.

## Dependency and approval flow

```mermaid
flowchart LR
    P0[Phase 0 documents] --> A0[User review and approval]
    A0 --> P1[Phase 1 foundation]
    P1 --> P2[Phase 2 identity/history]
    P2 --> P3[Phase 3 local MVP]
    P3 --> P4[Phase 4 public RAG]
    P4 --> P5[Phase 5 read-only tools]
    P5 --> P6[Phase 6 AWS pilot]
```

Every arrow after a phase also requires explicit user approval; diagram arrows are
dependencies, not permission. Use feature branches and PRs; Conventional Commits;
attach actual checks and risks; obtain approval before merge and before starting
another phase. No direct commits to main after initialization. Phase 0 ends after
documentation validation and local commits; no push, PR, merge, or Phase 1 work.

## Work breakdown and release evidence

Each milestone starts with issues containing observable acceptance criteria and a
bounded scope. PRs separate schema changes, API behavior, frontend UX and AI policy
where review benefits, while coordinating contracts. Implementation changes include
meaningful tests. Record architectural changes through ADRs, including rejected
alternatives and measured reasons. Do not copy coursework scripts or datasets.

Deliver an evidence bundle per milestone: commit IDs, test results, generated API
schema, reviewed fixtures/benchmark version, privacy/security decisions, measured
latency/cost where relevant, limitations, and rollback plan. Paid smoke evaluations
must be budget-limited and separately enabled; CI normally uses fakes/synthetic data.

## Risks and dependencies to resolve

| Dependency / risk | Owner / mitigation | Needed by |
| --- | --- | --- |
| Real pilot county/scope, participants, catalogue approval, staffing and operational budget | Owner-approved fictional/synthetic development proceeds; real owners/reviewers and resources must pass the pre-pilot gate | Before real pilot; deferred by owner on 2026-10-16 |
| Auth invitation delivery not selected | Engineer proposes one-time acceptance protocol and operator runbook; owner approves pilot participant handling | Phase 2 |
| No approved catalogue or bilingual benchmark | Department owners and English/Kiswahili reviewers prepare provenance-backed public material and independent cases | Phase 3 |
| Provider account/model, token budget and pricing approval | Owner chooses evaluated configuration and spend ceiling; engineer tests adapter capabilities and records actual rate assumptions | Phase 3 live calls |
| Sensitive data and overseas processing | County privacy/legal lead maps purposes, roles, locations, safeguards, retention and DPIA requirements | Before any real-data provider processing |
| Vector retrieval coverage and index compatibility | Engineer tests exact baseline, language slices, version/dimension isolation, future managed-DB extension support | Phase 4 |
| County API contracts/sandbox unavailable | Use fakes until official sandbox/authorization exists; do not invent production integrations | Phase 5 |
| AWS account, service/region/cost and operational owner | Owner approves deployment ADR; engineer validates managed DB/pgvector, restore, IAM and cost envelope | Phase 6 |

## Post-pilot, separately approved backlog

Public registration/email verification/recovery and staff SSO/MFA; Azure OpenAI and
Bedrock adapter parity; multi-county tenancy; human feedback/quality review workflow;
streaming/queues; staff-only RAG; multilingual voice/attachments; controlled record
updates with exact-action confirmation. Each requires contracts, permission/data
lifecycle review and acceptance evidence before activation. Fine-tuning or services
extraction require measured need rather than coursework precedent.

## Approved synthetic development and issue gates

The owner's amendment permits fictional county information only; no real citizen
records, county credentials, confidential documents, payments, public deployment or
live county integration. See [pre-pilot decision gate](PRE_PILOT_GATE.md). All
implementations require dedicated branches, tests, green relevant CI and the sole
maintainer's review before merging. A green check is not approval to merge/start
another issue. P1-03 is merged. P1-04 has explicit owner implementation approval and remains
pending review; P1-05 requires separate approval.

Phase 1 issues: [P1-01 backend](https://github.com/Abdalla-Wasaa/Production-Grade-County-Government-AI-Assistant/issues/2),
[P1-02 database/migrations](https://github.com/Abdalla-Wasaa/Production-Grade-County-Government-AI-Assistant/issues/3),
[P1-03 frontend](https://github.com/Abdalla-Wasaa/Production-Grade-County-Government-AI-Assistant/issues/4),
[P1-04 Compose](https://github.com/Abdalla-Wasaa/Production-Grade-County-Government-AI-Assistant/issues/5),
[P1-05 CI integration](https://github.com/Abdalla-Wasaa/Production-Grade-County-Government-AI-Assistant/issues/6),
[P1-06 acceptance](https://github.com/Abdalla-Wasaa/Production-Grade-County-Government-AI-Assistant/issues/7).
P1-01 provides dependency-free liveness, settings/lifecycle/error/logging foundations
and backend checks. P1-02 adds PostgreSQL sessions, baseline migrations, readiness
and real-database CI. P1-03 adds the independent bilingual frontend shell, with
draft Kiswahili copy behind human review before pilot. P1-04 adds the isolated
local Compose environment with explicit migrations, synthetic secrets and
disposable acceptance checks; domain/chat functionality remains excluded.

## P1-05 implementation scope

PR #12 is merged. The owner authorizes ci/p1-05-quality-gates for CI/tooling,
scoped backend typing, dependency/image audits, reporting, actual-Nginx browser
smoke, workflow-policy tests and daily security monitoring. Issue #6 is reopened
because previous completion markers lacked this milestone's evidence. Its exit
requires actual hosted context verification, negative-test evidence and explicit
residual-risk decisions; a green functional suite alone is insufficient.
GitHub required-check/ruleset configuration needs separate approval and remote
verification. No ruleset changes or P1-06 work are authorized. See [CI.md](CI.md).
