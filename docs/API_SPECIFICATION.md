# API specification

Status: Phase 0 contract baseline, amended 2026-10-16. P1-01/P1-02 implement only
GET /health/live and GET /health/ready, the error envelope, request IDs and local
CORS boundary. P2-01 adds nine auth endpoints only when explicitly enabled; isolated synthetic
validation is recorded in [the exposure report](P2_01_EXPOSURE_ASSESSMENT.md).
P2-03 persistence source is prepared under the owner-approved amendment below;
changed-runtime execution and policy acceptance remain pending.
Base path `/api/v1`; UTF-8 JSON, UUID IDs and UTC ISO-8601 timestamps. Pydantic
validates strict types, lengths, enums, and rejects unknown request properties.
No client can set ownership, roles, provider IDs, system instructions or usage.
The implemented OpenAPI document will be generated and checked against this baseline.

Related: [requirements](REQUIREMENTS.md), [database](DATABASE_DESIGN.md),
[security](SECURITY.md), [architecture](ARCHITECTURE.md).

## Common behavior

- Protected routes require `Authorization: Bearer <access_token>`; validate JWT,
  live session and active account. Unknown/other-user/expired conversation IDs all
  return 404. Missing/invalid authentication returns 401; known forbidden capabilities
  return 403. Admin role does not bypass conversation ownership.
- Generate a server trace ID for every response in `X-Request-ID` and error body;
  do not trust arbitrary client trace text. Responses containing personal data use
  `Cache-Control: no-store`. All unsafe requests with auth cookies use approved
  Origin/Referer validation and CSRF checks described below.
- Body cap 32 KiB, message length 1..4,000 Unicode characters after trim; NUL and
  invalid Unicode are rejected. `en` and `sw` are the only reply-language values.
  User/model text is rendered as plain text or sanitized Markdown without raw HTML.
- Lists: `limit` integer 1..100, default 20; opaque cursor, bound to filters and
  ordering. Invalid/tampered cursor =>422. Return `items` and `next_cursor` (null
  at end). Conversations order by `(updated_at DESC, id DESC)`; messages by
  `sequence ASC`. Conversation listings are best-effort under concurrent updates;
  clients deduplicate by ID. Message sequence is immutable.
- Validation =>422, missing resources =>404, conflicts =>409, rate/budget cap =>429
  with `Retry-After` when known, infrastructure unavailable =>503. No raw database
  errors, stack traces, SDK exception text or credential echoes.

Stable error envelope (including Pydantic validation, converted by an error handler):

```json
{
  "error": {
    "code": "validation_error",
    "message": "Check the request fields.",
    "request_id": "7df076dc-9d5c-4a55-95b2-9f2ec07e2ee8",
    "details": [{"field": "content", "code": "too_long"}]
  }
}
```

Messages are localized using `Accept-Language: en` or `sw` (default en), while
machine codes are stable. Do not include rejected values in validation details.

## Authentication contracts (invite-only pilot)

No public registration/provisioning endpoint in MVP. Approved operators create
accounts through a later audited procedure; invitations set a secure password,
notice acknowledgement and language preference before account activation. The
invitation delivery/acceptance mechanism must be finalized in Phase 2, not improvised
through shared passwords. Staff SSO/MFA and public recovery are later gates.

| Method / path | Request | Success | Failure |
| --- | --- | --- | --- |
| `GET /auth/csrf` | No body; approved browser origin | 200 `{ "csrf_token": "<opaque-signed-token>" }`, scoped CSRF cookie | 403 disallowed origin; 429 abuse |
| `POST /auth/login` | `{ "email": "pilot@example.invalid", "password": "<user-supplied>" }` | 200 token response; sets refresh cookie | 401 generic invalid credentials/disabled user; 403 CSRF; 422 fields; 429 abuse |
| `POST /auth/refresh` | Empty object; refresh cookie and CSRF header | 200 token response; atomically rotates refresh cookie | 401 invalid/expired/replayed session; 403 CSRF; 429 abuse |
| `POST /auth/logout` | Empty object; refresh cookie and CSRF header | 204 revoke current family and clear cookies; also 204 if already absent/revoked | 403 CSRF |
| `GET /auth/me` | Bearer | 200 current user | 401 |

Email length <=254, validated format and normalized consistently. Login password
length 1..128 characters (legacy/invalid values get generic denial); new pilot
password policy requires 12..128. Token response:

```json
{
  "access_token": "<short-lived-jwt>",
  "token_type": "bearer",
  "expires_in": 900,
  "user": {
    "id": "6de8a5bb-b4d3-430b-9e1d-3d6bb8aa7a9e",
    "email": "pilot@example.invalid",
    "role": "citizen",
    "preferred_language": "sw"
  }
}
```

`GET /auth/me` returns the same user object, not tokens/hashes. Access JWT contains
`sub`, `sid`, `iss`, `aud`, `iat`, `exp`, `jti`, `token_version`; server checks current
role and account state instead of treating stale role claims as authority.
Access lifetime 15 minutes; refresh family expires 7 days after login, does not
extend indefinitely, and can be revoked immediately. Frontend access tokens stay
in memory; after reload fetch CSRF then refresh. Serialize refresh in the browser.

Refresh cookie `county_refresh`: HttpOnly, Secure, SameSite=Strict, host-only,
Path=/api/v1/auth, Max-Age no later than family expiry. CSRF cookie `county_csrf`
is also host-only/Secure/SameSite=Strict/HttpOnly on that path. `GET /auth/csrf`
returns the associated signed, expiring token for memory storage; unsafe auth
requests send it as `X-CSRF-Token`. Validate signature, expiry, cookie/header match
and approved Origin (or same-origin Referer fallback); bind to session when present.
Missing browser origin evidence fails closed. CORS has no wildcard credential mode.
Development permits documented local cookie settings only on loopback. Bearer-only
conversation routes do not authenticate using these cookies.

## P2-01 authentication implementation (restricted synthetic validation)

The owner approved fixed roles, backend-first invite-only authentication and
synthetic operator-assisted recovery on 17 October 2026. The existing login,
refresh, logout, CSRF and current-user shapes above remain unchanged. The nine
route schemas, activation/reset behavior, session representations, status codes,
CSRF transitions and operator-only boundary are specified in
[AUTHENTICATION.md](AUTHENTICATION.md), with rationale in
[ADR 0002](DECISIONS/0002-invite-only-authentication.md).

Additional implemented routes are POST /auth/activate, POST /auth/logout-all,
GET /auth/sessions and DELETE /auth/sessions/{id}. All nine routes have real-PG
and actual Nginx acceptance evidence, without frontend authentication changes.
No public recovery/provisioning endpoint is added. Activation/reset never issues
login tokens. Unsafe session-management mutations require bearer and CSRF; list
and current-user reads use bearer only. Ordinary conversation ownership rules
remain unchanged and are outside P2-01 implementation.

## Conversation contracts

| Method / path | Request | Success | Important errors |
| --- | --- | --- | --- |
| `POST /conversations` | `{ "title": "Permit information", "language": "en" }`; both optional | 201 Conversation + `Location` | 422; 429 storage cap |
| `GET /conversations` | `limit`, `cursor` | 200 ConversationList | 422 |
| `GET /conversations/{id}` | UUID | 200 Conversation | 404 |
| `PATCH /conversations/{id}` | At least one of title/language; `If-Match` required | 200 updated Conversation | 404; 428 missing version; 412 stale version; 409 pending turn |
| `DELETE /conversations/{id}` | UUID, bearer | 204 atomic removal and cache invalidation | 404 (including repeated deletion); 503 DB unavailable |
| `GET /conversations/{id}/messages` | `limit`, sequence cursor | 200 MessageList | 404; 422 |
| `POST /conversations/{id}/messages` | `{ "content": "Synthetic service question" }` + required `Idempotency-Key` UUID header | 201 persisted user Message; 200 identical replay | 404; 409 conflicting key; 422; 429; 503 |

Title is trimmed nonblank 1..120 characters; language defaults to user preference
on creation. PATCH changes future reply language only; historical message language
is immutable. Phase 2 has no pending assistant work; unanswered user messages do not block
metadata changes or further user messages. Conversation creation, retrieval, PATCH, message listing and message writes return `ETag: "<version>"`; PATCH `If-Match`
uses that value. Expired conversations return 404 even before physical purge.

Conversation representation:

```json
{
  "id": "81fd20ee-2b9f-4a4c-afae-4acf65723aeb",
  "title": "Permit information",
  "language": "en",
  "version": 1,
  "created_at": "2026-10-13T10:00:00Z",
  "updated_at": "2026-10-13T10:00:00Z",
  "expires_at": "2026-11-12T10:00:00Z"
}
```

Do not return owner IDs or counters unnecessarily. List entries use the same shape.
Enforced Phase 2 caps: 100 unexpired conversations/user and 1,000 user messages per
conversation; return `storage_limit` when exceeded rather than silently deleting.

## Phase 2 user-message persistence (owner-approved amendment)

POST /conversations/{id}/messages stores one user message atomically. The request
body accepts only content; role, user_id, conversation_id, language, sequence and
other unknown fields are rejected (422), including an explicit role=user. Role is
always assigned as user by the server. Content is trimmed, nonblank, at most 4,000
Unicode characters; raw field length is also bounded at 4,000 before normalization.
NUL and invalid UTF-8/surrogate text are rejected. The shared 32 KiB body cap includes
chunked bodies. Titles similarly have a raw 120-character cap and are trimmed.
Optional creation title/language must be omitted rather than null; PATCH requires
at least one non-null field. Metadata GET and message history GET are separate
bounded resources; conversation retrieval never embeds unbounded message history.

First persistence returns HTTP 201 and this shape (also used in MessageList.items):

```json
{
  "id": "fded04d6-2d08-4c94-a024-74b49fd9e402",
  "conversation_id": "81fd20ee-2b9f-4a4c-afae-4acf65723aeb",
  "sequence": 1,
  "role": "user",
  "content": "Synthetic service question",
  "language": "en",
  "created_at": "2026-10-18T10:01:00Z"
}
```

An unanswered message is valid persisted history. Multiple unanswered messages are
permitted. No assistant placeholder, generation state, provider dispatch or fabricated
answer is created. Language is snapshotted from conversation preference on insertion.

Keys are scoped to the owned conversation and this persistence operation. Canonical
JSON of trimmed content is SHA-256 hashed. Same key/canonical content returns the
original message, HTTP 200 and Idempotency-Replayed: true, without changing version,
sequence, retention or language. Same key/different content returns 409
idempotency_conflict without modifying data. Same key in a different owned
conversation is independent. Missing/invalid keys return 422. A retry must reuse
the original key; clients must not invent a new key after an ambiguous timeout.

Account -> session -> conversation locks serialize concurrent requests. A unique
conversation/key constraint and conversation/sequence constraint are final guards.
First insertion increments next_sequence and version, updates activity/updated_at,
and recomputes expiry as min(creation+90 days, last accepted new user message+30 days).
Renames, reads and replays never extend expiry. DELETE atomically cascades messages;
expired, deleted, unknown and other-user conversation IDs return indistinguishable
404s. Storage caps return 429 storage_limit, without silently deleting history.

Bearer is the sole authentication mechanism for these endpoints. Scoped refresh
cookies cannot authorize them; auth CSRF/cookie behavior remains unchanged. All
responses remain no-store with generated request IDs and safe EN/SW errors.

## Phase 3 generation: separate future operation

The historical send/retry design reserved paired user/assistant rows as part of a
message write. This amendment supersedes that coupling. Generation must be a
separate operation; its endpoint, request/response, idempotency, retry, pending-state,
fencing, quota and recovery contracts require Phase 3 owner design approval.
No generation or retry endpoint is registered by P2-03. Existing persisted user
messages must remain valid without answers; Phase 3 must explicitly address choosing
which messages to answer and history/context selection without silently generating
answers for the Phase 2 backlog. Assistant schemas, citations and usage accounting
are future reviewed migrations, not fabricated fields on Phase 2 messages.

## Operational and deferred contracts

`GET /health/live`: 200 when process runs; no dependency calls or secrets.
`GET /health/ready`: 200 only when settings, migrations and database are ready;
otherwise 503 with generic status. No paid provider call in health probes. External
provider availability is measured separately. These two paths are outside `/api/v1`.
P1-02 returns `{"status":"ok"}` for both healthy operational probes. Readiness
returns the existing error envelope with code `service_unavailable`, empty details
and localized generic message on 503. It checks PostgreSQL and the single packaged
Alembic head under a complete-operation deadline, without exposing internal details
or applying migrations. Missing database URL is allowed at startup (live=200,
ready=503); malformed explicit configuration fails safely. See
[database operations](DATABASE_OPERATIONS.md). The local schema remains at
`/api/v1/openapi.json`. With auth disabled, no domain routes are registered. Validation error details currently use `field: request` and `code: invalid`
to avoid echoing untrusted keys/input. Exact `Accept-Language: sw` selects fixed
Kiswahili errors; other values default to English. See the
[backend guide](../backend/README.md) for local CORS and logging limitations.
Metrics are restricted to operator network/authentication, never a public history API.

Document ingestion/search, tool invocation, account provisioning, public registration,
feedback, streaming and record-changing actions have no MVP endpoints. Later phases
must specify schemas/authz/errors before implementation. A server-internal tool
dispatcher is not permission to expose arbitrary tools through HTTP.

## Phase 1 verification boundary

With auth disabled, OpenAPI paths remain exactly /health/live and /health/ready; the
document is served at /api/v1/openapi.json. Swagger/ReDoc UI is disabled. P2-01 adds nine optional auth endpoints; P2-03 adds the seven persistence handlers
on three paths when authentication is enabled. Their runtime verification is
separately gated. Authentication remains documented in AUTHENTICATION.md.
Verify liveness=200 without DB, readiness=503 without configuration/reachable current
schema, and readiness=200 only after explicit migration and runtime revision-table
access. Errors retain safe JSON, request IDs and no-store without connection details.
Nginx preserves these paths and error statuses; unknown API paths must not fall
through to SPA HTML. The historical Phase 1 shell issued no backend requests; P2-02 adds auth requests
only. Conversation history UI is outside P2-03.
Actual P1-06 evidence belongs in [Phase 1 acceptance](PHASE_1_ACCEPTANCE.md).
