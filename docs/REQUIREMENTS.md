# Requirements

Status: Phase 0 design baseline, amended 2026-10-16 for approved synthetic Phase 1
development. P1-01 implements the backend foundation; product requirements below
remain planned. Subsequent work requires approval under [AGENTS.md](../AGENTS.md).

## Purpose and scope

Help residents understand county services in English and Kiswahili, keep private
conversation history, and point them to reviewed official information. The assistant
does not issue permits, collect payments, adjudicate eligibility, or replace county
officers. The initial pilot serves one configured county; its identity, department
owners, source catalogue, and escalation contacts must be confirmed before release.
No real citizen records or coursework datasets are used for development. The owner
approved a fictional county environment with synthetic English/Kiswahili information
for initial development; a real county pilot is a separate approval gate.

Design inputs: [coursework review](COURSEWORK_REVIEW.md), user-selected stack,
[architecture](ARCHITECTURE.md), [API](API_SPECIFICATION.md), and
[security requirements](SECURITY.md). The stack is React/Vite/Tailwind CSS,
Python/FastAPI/Pydantic/SQLAlchemy, PostgreSQL, and initially OpenAI. Later phases
add pgvector, other provider adapters, and AWS deployment.

## Personas and permissions

| Persona | MVP permission | Boundary |
| --- | --- | --- |
| Citizen/pilot participant | Log in; manage own conversations; ask questions | No other user's history or privileged county data |
| Staff | Same personal conversation functions | No automatic access to citizen histories; staff document access is future work |
| Administrator | Account provisioning/deactivation through a controlled operator process | No general-purpose history-browsing API; audited exceptional support requires separate design |
| Department content owner | Review catalogue content through a documented offline process | Publishing through an administration UI is later work |

Pilot accounts are invite-only. Public registration, email verification, password
recovery, staff federation, and privileged MFA are required before broad public
onboarding, but are outside the closed pilot MVP. Never ship demo credentials.

## MVP functional requirements

| ID | Requirement | Acceptance evidence |
| --- | --- | --- |
| FR-01 | Login, session renewal, logout, and current-user identity | Contract tests cover valid/invalid/expired/revoked sessions and disabled accounts |
| FR-02 | Create, list, read, rename, and delete owned conversations | Cross-user tests return indistinguishable 404; deletion removes messages and cached context |
| FR-03 | Persist ordered user messages and assistant attempts; recover failed turns | Idempotency, simultaneous sends, timeout, retry, and restart tests match the API state machine |
| FR-04 | Answer within a reviewed, versioned public service catalogue | Use a small bounded catalogue of approved service cards with official URLs and review dates; give no unsupported fee, deadline, eligibility, or legal claim |
| FR-05 | Abstain and provide reviewed escalation information outside evidence/scope | Missing, expired, ambiguous, and out-of-scope cases disclose uncertainty; do not invent contact details |
| FR-06 | Explicit `en`/`sw` interface and reply preference; accept mixed-language input | Bilingual reviewer tests cover both languages, code switching, and preserving names, numbers, and official titles |
| FR-07 | Resume bounded, private conversation context | Another user's history never enters prompts; changing languages does not reset history; deleted content cannot reappear |
| FR-08 | Accessible responsive React UI with clear error and pending states | Keyboard navigation, labels, visible focus, mobile layout, and screen-reader status announcements tested |
| FR-09 | Show AI limitations, source references, and privacy notice before first use | User sees information-only scope and approved escalation route in both languages |
| FR-10 | Handle rights requests through a verified operator process | Document access/correction/objection/deletion handling; do not promise blanket erasure or copy chat contents into support logs |

The MVP catalogue is a small configuration-managed dataset, not document RAG or
an unrestricted knowledge base. Selection is deterministic from approved topic
tags/terms; no match means abstention. Evidence IDs are checked server-side against
the selected cards. Generated text remains subject to evaluation and review:
attaching a valid URL alone does not prove every claim is supported.

## Future capabilities and exclusions

| Phase | Capability | Gate |
| --- | --- | --- |
| 4 | Approved public document ingestion, pgvector retrieval, versioned page/section citations | Source ownership, security review, bilingual retrieval benchmark, and deletion tests |
| 5 | Allowlisted read-only county tools, e.g. service-directory lookup | Server-side authorization, argument/output validation, audit, bounded execution |
| 6 | AWS deployment and operational pilot | Privacy/transfer decision, restore/rollback tests, identity and monitoring readiness |
| Later separately scoped | Azure OpenAI/Bedrock adapters; staff-only documents; public onboarding; streaming; feedback workflow | Adapter parity, access review, contracts and benchmark evidence |
| Later separately scoped | Multiple counties, voice, attachments, government record updates, payments | New tenancy/privacy/threat model and explicit approvals; human confirmation for consequential actions |

No autonomous legal decisions, benefit eligibility decisions, financial transactions,
unrestricted web browsing, citizen uploads, fine-tuning, or production system writes
are part of the MVP. General model knowledge cannot stand in for current county policy.

## Nonfunctional requirements

Targets below are proposed pilot acceptance targets, not measured performance or
contractual SLAs. Record hardware, provider model, sample size, load, and failure
rates with measurements; change targets only through a reviewed decision.

| ID | Requirement | Proposed gate |
| --- | --- | --- |
| NFR-01 | Security and ownership | All protected-route and cross-user denial tests pass; no unresolved critical/high security findings |
| NFR-02 | Privacy | Approved notice, retention schedule, controller/processor mapping, transfer assessment, and redacted-log checks before real personal data |
| NFR-03 | API performance | At 10 concurrent pilot users, non-AI API p95 <=500 ms on defined test hardware; assistant end-to-end p95 <=15 s, hard generation deadline 30 s |
| NFR-04 | Reliability | Durably recorded pending/completed/failed attempts; stale work recovered within 60 s; no duplicate turns on replay; pilot objective 99.5% monthly availability after AWS milestone |
| NFR-05 | AI quality | At least 100 reviewed held-out cases, at least 40 per language; >=90% useful supported answers per language and >=95% correct abstention on unsupported cases; report denominators and uncertainty |
| NFR-06 | Sensitive facts | Zero unsupported fees/deadlines/eligibility claims in the release benchmark; any observed failure blocks release pending remediation |
| NFR-07 | Cost and limits | 4,000-character message cap; 2,000-token output reservation; 8,000-token input budget; enforce per-user/global budgets before dispatch; proposed USD 20/day pilot cap pending owner approval |
| NFR-08 | Observability | Trace every request/attempt without content; provider errors, token usage, latency, rejection, expiry, and deletion metrics visible to operators |
| NFR-09 | Reproducibility | Locked dependencies, migrations, provider/prompt/catalogue versions; synthetic fixtures; CI lint, types, tests, security and evaluation gates |
| NFR-10 | Recovery | Proposed AWS RPO <=24 h and RTO <=4 h; demonstrate restore and replay of deletion records before pilot launch |
| NFR-11 | Accessibility | WCAG 2.2 AA as design/testing target; bilingual UX and low-bandwidth error handling; independent accessibility review before public launch |

Client requests default to 10 sends/minute/user with a burst of 3, plus operator-set
IP/global controls; login has stricter abuse controls in [SECURITY.md](SECURITY.md).
Rate limits, storage caps, and budgets must be configurable and enforced across API
workers. Quotas include failed provider attempts where charges are possible.

## Tests and release evidence

Require backend unit tests for policy/context/provider mapping; PostgreSQL integration
tests for migrations, ownership, sessions, concurrency, expiry and cascade deletion;
API contract tests for JSON schemas/statuses; React component and end-to-end tests
for login, language choice, conversation lifecycle, failure and retry. Use provider
fakes for normal CI and opt-in budget-limited live smoke tests. RAG/tools receive
their own adversarial and authorization suites before activation. A single coverage
percentage is not a substitute for risk-based cases.

## Decisions requiring owner confirmation

The owner's 2026-10-16 amendment defers real county selection, participants, service
catalogue approval, staffing and operational budget to the explicit
[pre-pilot gate](PRE_PILOT_GATE.md); they do not block synthetic Phase 1 work.
Before any live provider calls, separately approve account/model configuration,
privacy basis, permitted data categories and spend. Before any real pilot, confirm
the gate's content/privacy/security/hosting/retention and operational decisions.
No public deployment, live county integration, payments or real/confidential records
are authorized. See [roadmap](ROADMAP.md) for milestone boundaries.

Approved foundation stack: Python 3.12; uv with committed uv.lock; FastAPI/Pydantic v2;
Node.js 24 LTS; React/Vite/TypeScript/Tailwind CSS; PostgreSQL 17; SQLAlchemy 2.x and
Alembic; Pytest/Ruff; Vitest/React Testing Library/ESLint; Docker/Compose and GitHub
Actions. Exact package compatibility is checked before installation/locking and
verified by relevant tests. Public-pilot review is not satisfied by synthetic tests.

## Owner-approved WhatsApp-first planning amendment — 22 October 2026

[ADR0006](DECISIONS/0006-whatsapp-first-framework-adapters.md) extends the target
channels: WhatsApp is primary for citizens; React remains an alternative citizen
channel and a future operator/admin workflow client. Original FR/NFR IDs and release
gates above remain traceable and mandatory. No existing feature is deprecated.
The current React/auth/history implementation remains supported; WhatsApp is not
implemented, public onboarding is not approved, and no phone identity replaces a
verified user or operator authority. Existing invite-only development stays intact.

Proposed additional channel criteria for subsequent contract approval:

- CH-01: shared domain ownership/content/language semantics across adapters; pass
  cross-channel isolation and no phone/email auto-link tests before any linked access.
- CH-02: verify webhook challenge and raw-body signatures, business scope, durable
  deduplication, status replay/order, unsupported content and bounded ingress; never
  acknowledge non-durable work as accepted. Mock Meta in CI.
- CH-03: durable inbox/outbox, explicit unknown-send outcome, bounded retry/leases,
  account/consent/window rechecks, recovery and deletion/hold tests; no exactly-once
  external-delivery claim or unbounded agent worker.
- CH-04: reviewed privacy notices, language choice, permitted messaging templates,
  opt-out and human escalation; authenticate link/unlink and retain minimal proof.
- CH-05: proposed operator UI has separately approved privileged auth/server APIs;
  citizen/staff/admin JWTs do not grant history browsing or source publication.
- CH-06: framework adapters preserve AIProvider and source/retrieval contracts;
  no implicit remote telemetry, framework memory or bypass of budgets/authorization.

These are proposed design/test requirements, not authorized endpoints or runtime.
NFR-03 latency, NFR-05/06 bilingual quality/sensitive claims, Phase4 retrieval gates,
#39 independent review and #44 deferred generation all remain unresolved where
previously unmet. Read-only MCP is proposed under the existing Phase5 tools gate;
state-changing tools need separate approval and exact human confirmation. No live
WhatsApp, real data, RAG ingestion, model download or production approval follows.
