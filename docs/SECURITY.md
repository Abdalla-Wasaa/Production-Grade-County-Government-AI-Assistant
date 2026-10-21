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
unfixed findings. The historical P1-04 fixable-only gate could be green despite
unfixed findings; P1-05 superseded it with exact-inventory and expiring-decision
checks. Residual-risk acceptance requires explicit maintainer review; public/production/
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

## P1-06 acceptance and daily human review

Ruleset 25222082 now enforces all seven app-bound checks, strict current branches
and resolved conversations; controlled PR #15 verified pending/failing blocking and
a clean passing state without merging. Earlier fixable-only scan-policy statements
are historical; current P1-05 policy retains all findings and exact-inventory gates.

Technical foundation acceptance can only authorize restricted synthetic development,
never production security approval. The baseline/acceptance files remain unchanged,
with 115 HIGH and 3 CRITICAL occurrences and expiry 23 October 2026, 23:59 EAT.
No renewal, real data, public deployment or later phase is implied. The owner is
responsible for daily human CRITICAL review. Until an actual dated review reference
is supplied, mark that obligation pending; a scanner or agent does not perform it
on the owner's behalf. Do not fabricate or backdate review records.

[Phase 1 acceptance](PHASE_1_ACCEPTANCE.md) separates automated evidence, human review,
isolation limitations and remaining approval gates. A failed or unavailable required
verification blocks that acceptance item even when CI is green.

## P2-01 approved direction and changed-exposure gate

Phase 1 technical closure and actual 17 October owner CRITICAL review are recorded
in [acceptance history](PHASE_1_ACCEPTANCE.md). Historical pending-review statements
above are superseded for that date only; subsequent daily human review remains due.
The owner authorized fixed-role invite-only backend auth, synthetic operator-assisted
reset, no live email and no public registration. See [ADR 0002](DECISIONS/0002-invite-only-authentication.md)
and [authentication contract](AUTHENTICATION.md). The P2-01 backend endpoints are
implemented and have passed isolated synthetic validation; frontend auth is excluded.

The Phase 1 exception is NOT approval of changed auth code or migrations. The policy
hash includes application, migration, frontend, dependency and infra bytes. Preserve
the existing baseline/acceptance records and expiry (23 October 2026, 23:59 EAT).
Prepare source-level work only after contract merge; assess changed paths, dependencies,
full built-image findings and newly reachable surfaces before running changed code
under an exception. A required owner decision must be explicit; do not rewrite the
hash or broaden acceptance to obtain green CI. If blocked, retain source/static work,
report runtime/security checks pending and do not bypass seven-check enforcement.
No public deployment, real records, production credentials or live integrations.


### Separate P2-01 owner decision — 17 October 2026

The owner explicitly approved the reviewed PR #24 implementation and exact exposure/
backend inventory documented in [P2-01 assessment](P2_01_EXPOSURE_ASSESSMENT.md).
This supersedes the earlier source-only execution gate for that exact candidate.
The original Phase 1 records remain unchanged in the
[historical snapshot](security/p2-01/phase-1-policy-snapshot.json); the active records
carry a separate P2-01 decision, not a reattributed or renewed Phase 1 approval.
All 118 package/CVE occurrences remain individually enumerated; none is suppressed.
Only backend scan identity/report provenance and its complete 119-package inventory
change. No vulnerability row, severity, fix status or base-image pin is changed.

Expiry stays 23 October 2026 at 23:59 EAT (20:59 UTC). Daily human CRITICAL reviews
remain required and must be recorded truthfully. A fix, new finding, severity increase,
KEV listing or further exposure/dependency change invalidates the applicable decision.
Synthetic isolated local development only; no real county/citizen data, production
credentials, public or production deployment. Scanning, all seven required contexts,
strict branch protection and normal PR review remain active. Green development CI
is not production security approval or authorization to merge.


### Separate P2-02 owner decision — 17 October 2026

The owner explicitly approved tested PR #25 source 2a33394 and exposure
0b8f2dc7e55e72fbc96325edbec4d57a5a97c9eb52d4fae3251e9aec302b958d,
with unchanged full dependency inventories and all 118 inherited findings
(115 HIGH/3 CRITICAL) individually enumerated in the existing bound baseline.
See [P2-02 evidence](P2_02_EXPOSURE_ASSESSMENT.md). The active decision is separate
from P2-01, whose original approval bytes are preserved in the
[P2-01 acceptance snapshot](security/p2-02/p2-01-acceptance-snapshot.json).
No baseline, inventory, vulnerability row, scanner rule, workflow or ruleset changes.

This is isolated synthetic local development only. Expiry remains 23 October 2026
at 23:59 EAT (20:59 UTC). Daily human CRITICAL reviews must continue truthfully.
Any available fix, new finding, severity increase, KEV listing or further exposure/
dependency change invalidates the applicable decision. No automatic expansion or
renewal. No real citizen/county data, production credentials or public/production
deployment. All seven required checks, vulnerability scanning, strict branch
protection and normal owner PR review remain active. No merge is authorized.

## Owner-approved P2-03 records, 18 October 2026

The owner explicitly approved the seven-file update for f9520eb932341a150f26ea1d977b8fff67a51c7d,
exposure 88669fbe4cfafc7dc45e6775546e44e6ca8bcbec1dcacfb0f89a36c702af19b4,
web inventory 21 packages and unchanged 115 HIGH/3 CRITICAL inherited occurrences.
Previous P2-02 policy bytes are preserved in docs/security/p2-03/p2-02-policy-snapshot.json.
Expiry remains 23 October 2026, 23:59 EAT. Synthetic isolated local development only;
no real data or production deployment. All invalidation triggers, seven checks, scans,
branch protection and owner PR review remain mandatory. Push and PR linked to issue
19 are now authorized; no merge. Human CRITICAL review for today remains pending: no
review completion is asserted. Automated policy does not require a human-review
timestamp before CI; documented human acceptance obligations remain incomplete even
if CI passes. This approval does not grant unconditional milestone acceptance.

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

## P2-05 source preparation and engineering policy — 19 October 2026

The owner approved implementing the existing 30-day inactivity/90-day absolute
expiry, daily 02:00 Nairobi maintenance with catch-up, authorized audited 30-day
hold reviews, verified operator-managed account deletion with immediate revocation,
and synthetic two-working-day acknowledgement/seven-calendar-day eligible completion
targets. These are engineering targets, not legal deadlines or real records authority.
[Privacy runbook](PRIVACY_LIFECYCLE.md) defines hold restrictions, authorization,
conditional purge availability/capacity assumptions, failure alerts and recovery.

An owned held conversation DELETE is explicitly 409 deletion_restricted, not a false
204. Expired/other-user IDs remain 404. Operators authenticate as explicitly enrolled
PostgreSQL roles, not claimed names/JWT admin roles. No public admin API is added.
Audit records contain only fixed actions, bounded pseudonyms/correlation IDs; no
body, email, IP, credentials or free-form legal documentation. Holds never auto-release.

This engineering authorization is not a P2-05 vulnerability acceptance or permission
to execute changed code. Before running it, record the exact commit/exposure, compare
complete inventories/findings, and obtain explicit isolated synthetic authorization.
The P2-04 exception does not cover this changed exposure. Its existing expiry remains
23 October 2026, 23:59 EAT. All seven checks, scans, exposure/inventory gates and branch
protection remain active. Today's actual human CRITICAL review is unconfirmed.
No real data, production credentials/deployment, automatic renewal or merge.


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

## Dated P2-06 human review status — 19 October 2026

The owner explicitly confirmed personal review of the three existing CRITICAL
assessments on 19 October: “I reviewed all three today; continue restricted acceptance”.
See [dated evidence](security/p2-06/human-critical-review.json) and
[Phase 2 verification](PHASE_2_ACCEPTANCE.md). This supersedes older pending-review
statements for that day only; daily review remains necessary on subsequent days.
No active acceptance or historical snapshot changed; scope, invalidation rules and
23 October 2026, 23:59 EAT expiry remain unchanged. Production stays prohibited.

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
