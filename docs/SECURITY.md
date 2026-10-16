# Security, privacy and operational assurance

Status: Phase 0 requirements, amended 2026-10-16. P1-01/P1-02 implement local
configuration/HTTP/logging boundaries and restricted database/migration infrastructure; other product controls remain planned and
no compliance certification is claimed. Applies to the [MVP](REQUIREMENTS.md) and later RAG/tools defined in
[architecture](ARCHITECTURE.md). [Database](DATABASE_DESIGN.md) and
[API contracts](API_SPECIFICATION.md) specify enforceable state and permissions.

## Kenya data-protection considerations

The Act's sections 25/26 address processing principles and subject rights; section
30 concerns lawful processing, 31 impact assessment, 35 significant automated
decisions, 41 safeguards, and 48/49 overseas transfers. Section 43 requires qualifying
controller breach notification without delay within 72 hours; processors notify
controllers without delay and, where reasonably practicable, within 48 hours.
Apply the section's harm threshold and communication duties rather than treating
every operational error as a notifiable breach.
[Data Protection Act, Kenya Law](https://new.kenyalaw.org/akn/ke/act/2019/24/eng%402022-12-31/source).

ODPC describes transparency, minimization, accuracy, limited retention, transfer
safeguards, and rights to information, access, objection, correction and specified
deletion. These are the basis for the product controls below, not a blanket right
to erase every government record.
[ODPC rights and principles](https://www.odpc.go.ke/rights-of-a-data-subject/).
Review high-risk processing with the county privacy officer using
[ODPC DPIA guidance](https://www.odpc.go.ke/wp-content/uploads/2024/02/ODPC-Guidance-Note-on-Data-Protection-Impact-Assessment-1.pdf)
and confirm applicable registration responsibilities using
[ODPC registration guidance](https://www.odpc.go.ke/wp-content/uploads/2024/02/ODPC-Guidance-Note-on-Registration-of-Data-Controllers-and-Data-Processors.pdf).

Sources were checked during Phase 0. Kenya Law full-text retrieval returned 403;
official indexed material and accessible ODPC guidance informed this planning
summary. County legal/privacy review must confirm current text, regulations,
assessment/notification deadlines, and applicability before real-data operation.
Do not represent this design as legal approval or proof of compliance.

## Governance gates before real personal data

Appoint the county service owner and privacy lead. Record who determines purposes
and means (anticipated county controller), which engineering/hosting/AI suppliers
process on instructions, contractual duties, subprocessors and approved locations.
Verify these roles rather than assigning all vendors the same label.

The privacy lead approves purpose and lawful basis per activity: account/session
management, stored chats, AI processing, audits and analytics. Do not equate a
privacy-notice checkbox with valid consent or use consent as the automatic basis
for all public services. Publish bilingual notices with collected categories,
purpose, recipients, retention, rights contact, and AI limitations. Never generate
the official rights contact from model knowledge.

Conduct DPIA screening and a DPIA where applicable, before enabling real-data AI,
restricted documents or consequential actions. Confirm any submission/consultation
requirements and lead times in the legal review. Keep evidence and mitigation owners.
Public access is not permission to reuse personal details embedded in public documents.

For overseas AI/hosting processing, document data-flow locations, contracts,
safeguards, access, subprocessors and applicable transfer basis. Region names alone
are insufficient. OpenAI `store: false` disables the chosen response-storage behavior,
not every category of provider retention; account-specific controls and eligibility
must be assessed using [official OpenAI data controls](https://developers.openai.com/api/docs/guides/your-data).
Sensitive or unsupported data classes are not sent until specifically approved.
No automatic switch to another provider/location on outage.

## Threat model and required controls

| Threat / boundary | Controls | Verification |
| --- | --- | --- |
| Cross-user chat access | Ownership predicate on every read/mutation; live account/session checks; 404 for unknown/other-user resources | Random IDs, list pagination, retry, delete and expired-resource isolation tests |
| Stolen/replayed credentials | Argon2id passwords; short-lived JWT; hashed rotating refresh tokens; session family revocation and account token version | Expiry, logout, disable, refresh race and reuse tests |
| XSS / unsafe model text | Plain text or sanitized Markdown; no raw HTML; safe URL policy; CSP; no tokens in localStorage | Malicious message/citation rendering and browser tests |
| CSRF / malicious origin | Same-origin deployment, scoped secure cookies, signed CSRF header/cookie check on auth writes, strict CORS | Missing token, foreign Origin, stale signature and cookie path tests |
| Injection into prompts/retrieval | Separate instructions from content; no trust in model role/IDs; source registry; tool allowlist | Direct/indirect injection, multilingual overrides, fake citations and secret-exfiltration cases |
| Expensive abuse / resource exhaustion | Shared rate/concurrency/storage/budget limits; message/body/token caps; deadlines and bounded retries | Multi-worker quotas, long Unicode input, timeout, SDK retry and circuit-breaker tests |
| SQL injection / unsafe DB permissions | Parameterized SQLAlchemy queries; least-privilege runtime role; reviewed migrations | Repository tests, privilege assertions and migrations on PostgreSQL |
| Secret/supply-chain leaks | Backend-only secrets; CI scanners; locks; reviewed pinned actions/images; least-privilege workflow tokens | Scan tracked files/history and built assets/images; inspect fork-PR permissions |
| Future ingestion SSRF / malicious files | Operator-only allowlisted sources, redirected-host/IP checks, scanning and isolated extraction | Private-IP/redirect/path traversal/malware/oversize fixture tests |
| Future unauthorized tools | Server-derived actor/scope, schema and output validation, permission check on every call | Unlisted names, tampered scope, invalid args, denied targets and replay tests |
| Deleted data resurfacing | Query expiry, cascade purge, no chat vectorization, derived-data invalidation, restore deletion replay | In-flight deletion, retry after deletion, cache and restored-backup tests |

Security decisions are enforced outside model prompts. Regexes and instructions
can add defenses but cannot guarantee safety. A response containing an official
URL is not evidence that its claims are correct.

## Identity and browser controls

Invite-only accounts require a verified operator workflow and unique user-selected
passwords; Phase 2 must document secure acceptance, one-time delivery, expiry and
activation before provisioning real accounts. Never email reusable plaintext passwords
or use shared demo accounts. New passwords 12..128 characters; reject known-compromised
values through an approved method without leaking passwords. Use Argon2id parameters
benchmarked on deployment hardware; rehash on login when policy changes.

JWT signing uses an explicit allowlisted algorithm and a high-entropy backend secret
in the closed pilot; verify issuer, audience, expiry, subject, session ID and version.
Plan asymmetric issuer/federation keys before staff SSO; do not accept arbitrary
algorithm or JWKS URLs from tokens. Validate active user and session on every request
for immediate revocation. Role changes/credential compromise increment token version
and revoke all families. Signing-key rotation must be documented and tested.

Use the [API cookie/CSRF contract](API_SPECIFICATION.md) exactly; Secure is required
outside loopback development. Login returns one generic denial and equalized handling
for missing/disabled/invalid users; never log a password or bearer token. Initial abuse
policy: five failed logins per account per 15 minutes and 20 per IP per 15 minutes,
progressive delays with no permanent denial trap; tune against abuse and shared NATs.
Implement counts centrally, not per process. Privileged public access requires MFA
and recovery; public self-registration requires email verification and reviewed
account-recovery contracts before launch.

Serve TLS, HSTS after deployment validation, strict content security policy,
frame restrictions and minimal allowed origins. Sanitize link rendering; use
`noopener` for new-window external links. Disable analytics that capture form/chat
content, session replay and browser persistent chat caching.

## Privacy lifecycle and proposed retention

These durations are engineering proposals requiring controller approval; they are
not statutory defaults. Delete earlier when purpose ends unless an applicable,
documented obligation/hold requires retention. Roles and UUIDs are still personal
data where linkable. Develop only with synthetic records.

| Data | Proposed retention / behavior |
| --- | --- |
| Accounts | While active and required for the pilot; deactivation immediately revokes sessions; verified deletion is processed through privacy workflow |
| Conversations/messages | Inaccessible after earliest of 30 days without a new user turn or 90 days from creation; physical purge within 24 h; user conversation deletion removes live rows immediately |
| Pending attempts | 45 s lease; recovery within 60 s after expiry; failed attempt metadata expires with conversation |
| Sessions and refresh hashes | 7-day absolute family lifetime; consumed hashes retained until expiry for replay detection; purge within 24 h afterwards |
| Application operational logs | 14 days, no chat/credentials; minimize IP collection and restrict access |
| Security audit records | 90 days, purpose-limited actor pseudonym, action/outcome/time; no body; extend only under approved incident hold |
| Usage accounting | 90 days of minimal noncontent accounting; reconcile billing, restrict linkability and purge identifiers when no longer needed |
| Backups | Encrypted rolling 30-day window; restore only in isolated environment; replay current deletion ledger before access |
| Deletion ledger | Minimal object IDs/deletion times through backup window plus 7 days; no deleted content; scoped access |
| Public knowledge sources later | Versioned review/withdrawal policy by owner; no indefinite retention of restricted/personal material |

Account rights are not reduced to conversation DELETE. Establish verified access,
correction, objection and deletion requests with secure exports, receipt, assessment,
response deadlines confirmed by privacy lead, and appeal/escalation. A minimal
case log holds request status, not conversation dumps. Account deletion invalidates
sessions and removes associated chats/derived artifacts subject to approved holds.
Backups and supplier retention are explained transparently; live deletion is not
instant erasure from every backup/provider. Do not restore expired/revoked access.

Conversation context must be minimized before provider dispatch. Exclude account
email, session data, unrelated turns, and unapproved sensitive content. If detected
sensitive data cannot be safely handled, decline transmission and direct to reviewed
official channels. Redaction is imperfect: notices, purpose limits, restricted
logging, provider controls and test evidence remain necessary. Do not retain a
plaintext PII mapping or infer a long-term profile from chats.

## Observability and incident response

Record generated request/attempt IDs, route template (not personal URL/query data),
status/error category, language, duration, token counts, provider/model/prompt/corpus
versions, and circuit/quota outcomes. Never put user IDs or message text into metric
labels; avoid unbounded cardinality. Restricted metrics cover p95 latency, failures,
abstentions, retrieval misses, queue/lease expiry, usage/spend, auth denial, purge
success and DB saturation. Structured logs and traces redact headers by default.

Alerts identify spend exhaustion, persistent provider/DB failure, failed purges,
unusual login/authorization denial and degraded answer quality. Name an operational
owner and an escalation channel before deployment. Live/ready probes make no paid
AI calls. Sensitive audit writes use a durable restricted append-only sink, distinct
from ordinary debug logs, with access and alteration monitoring.

Incident runbooks: isolate the affected flow, revoke credentials/sessions, preserve
minimal evidence, stop inappropriate processing, assess harm with the privacy lead,
record awareness times, notify relevant controller/authority/subjects when required,
and document recovery. Target internal escalation within one hour of suspected
personal-data exposure; this is an engineering goal, not the statutory deadline.
Exercise token/key rotation, provider shutdown, restore and deletion replay before
real-data pilot. No automatic restart that re-enables an unsafe provider flow.

## Verification and release gates

CI must run synthetic unit, contract, PostgreSQL integration, frontend and security
tests plus bilingual offline evaluations; no paid calls or production data in routine
PR jobs. Secret/dependency/image scans and type/lint checks gate merges. Restrict
GitHub Actions token permissions, pin reviewed actions, and never expose secrets to
untrusted fork code. Deployment credentials later use approved short-lived workload
identity rather than long-lived keys in repository settings where possible.

Before launch: resolve critical/high findings; validate ownership and session matrices;
review privacy/data-flow/DPIA evidence; evaluate both languages; verify unauthorized
tools and sources remain unavailable; measure budgets/deadlines; restore backup and
reapply deletion; document residual risks and obtain county owner/user approval.
No compliance, penetration-test, production SLA or deployment claim is made in Phase 0.

## P1-02 database credential boundary

Runtime and migration credentials are separate. Runtime needs CONNECT, schema USAGE
and SELECT on `public.alembic_version` only. No DDL, revision mutation or superuser
privileges. Privileged migrations are explicit operator actions; neither HTTP nor
startup applies migrations. URL values are secrets, excluded from model repr/JSON
and error/log output. Query echo is off and SQL parameters are hidden. Only supported
URL options are accepted, preventing connection/statement logging option injection.
No real county database is authorized. Integration fixtures require disposable
loopback PostgreSQL 17 and create/remove only recorded random databases/roles.
See [database operations](DATABASE_OPERATIONS.md). These controls do not certify
production TLS, backup/recovery, privacy compliance or vulnerability-free packages.

## P1-03 browser foundation

The shell renders text only, validates public same-origin API paths, and makes no
backend/provider requests. No auth tokens, messages or personal records are stored;
only the `en`/`sw` preference is saved locally, with safe storage-denial handling.
Vite loads frontend-local environment files; every exposed VITE_ value is public.
No database/provider credentials belong in browser configuration or bundled assets.
Fixed error-boundary messages replace exception output; React's default exception
reporting is disabled at the root. No telemetry or remote assets are introduced.
Future diagnostic reporting needs its own privacy review. Kiswahili draft copy and
actual browser/screen-reader accessibility remain pre-pilot review obligations.
See [frontend verification](FRONTEND_VERIFICATION.md).

## P1-04 container controls

The local stack binds web to loopback only, isolates database traffic on an internal
network, drops all capabilities, uses non-root UIDs and read-only root filesystems,
and bounds writable tmpfs, CPU, memory, PID counts and rotating logs. Runtime,
migration and bootstrap credentials are independent and mounted per service.
File-backed Compose secrets rely on private host parent directories, not encryption;
Docker/host administrators remain trusted. No automatic credential rotation or
volume deletion is allowed. Reset requires exact confirmation and matching resource
ownership labels. See [Compose development](COMPOSE_DEVELOPMENT.md) for the trust
model and [image findings](CONTAINER_IMAGES.md) for remaining upstream OS risks.
These controls do not approve a public or real-data deployment.

## P1-04 residual vulnerability gate

The dated [vulnerability register](VULNERABILITY_REGISTER.md) retains every reported
HIGH/CRITICAL package/CVE occurrence, distinguishes vendor applicability from
confirmed exploitation, and records owner/review triggers. No known-exploitation
absence or local-only configuration constitutes a waiver. Complete reports include
unfixed findings even though CI's existing fixable-finding gate can be green.
Residual-risk acceptance requires explicit maintainer review; public/production/
real-data use remains blocked pending separate security clearance.

## P1-05 automated development gates

[CI policy](CI.md) adds seven stable PR contexts and a separate daily monitor.
Runtime/dev/tool Python dependencies are audited; Node audit remains active. Complete
image findings are preserved and fail for new/fixable/escalated/known-exploited
records, invalid evidence or absent/expired owner acceptance. The baseline is not
an exception list. Decisions bind the exact baseline hash, approved scope, actual
owner reference, exposure hash and expiry. Changed application/infrastructure
exposure requires another owner review. No acceptance is automatically created or renewed.

The Trivy process ignores repository override files and inherited TRIVY_* options.
Reports bind the immutable built image ID and recorded runtime base pin; a retagged
image or mismatched scan identity fails. Scan errors never count as clean images.
CI policy/source changes require explicit human review; a self-edited workflow or
approval metadata cannot cryptographically prove owner authorization.

The sole maintainer must approve any residual development risk. No secret/model/
AWS credentials, publishing or deployment permissions are required. Production
remains blocked even if every development check passes. GitHub ruleset changes
remain a separately approved operation after actual contexts are verified.

### P1-05 audit remediation controls

The follow-up fixes missing hosted artifact uploads and makes required evidence
absence fail. Reviewed hidden report directories are explicitly included; raw logs,
environments, credentials and database volumes remain excluded. Workflow command
and artifact contracts detect removal, no-op replacement and configuration bypass.
Scanner identity, immutable image identity, full package inventories and exact
HIGH/CRITICAL occurrence counts are checked against reviewed evidence. Duplicate
or truncated evidence fails closed. Independent monitoring stages record failures
and continue remaining safe checks; partial results never count as success.
See [CI remediation details](CI.md#p1-05-audit-remediation).

The original 118-occurrence baseline and explicit owner acceptance are unchanged.
Expiry remains 23 October 2026 at 23:59 EAT; there is no new approval or renewal.
Production/public/real-data use remains blocked. Daily automated monitoring provides
evidence, while human CRITICAL review and investigation of failed runs remain required.
