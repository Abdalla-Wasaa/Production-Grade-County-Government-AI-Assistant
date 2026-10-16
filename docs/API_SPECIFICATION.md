# API specification

Status: Phase 0 contract baseline, amended 2026-10-16. P1-01 implements only
GET /health/live, the error envelope, request IDs and local CORS boundary. Readiness,
authentication and conversation endpoints remain unimplemented.
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

## Conversation contracts

| Method / path | Request | Success | Important errors |
| --- | --- | --- | --- |
| `POST /conversations` | `{ "title": "Permit information", "language": "en" }`; both optional | 201 Conversation + `Location` | 422; 429 storage cap |
| `GET /conversations` | `limit`, `cursor` | 200 ConversationList | 422 |
| `GET /conversations/{id}` | UUID | 200 Conversation | 404 |
| `PATCH /conversations/{id}` | At least one of title/language; `If-Match` required | 200 updated Conversation | 404; 428 missing version; 412 stale version; 409 pending turn |
| `DELETE /conversations/{id}` | UUID, bearer | 204 atomic removal and cache invalidation | 404 (including repeated deletion); 503 DB unavailable |
| `GET /conversations/{id}/messages` | `limit`, sequence cursor | 200 MessageList | 404; 422 |
| `POST /conversations/{id}/messages` | Send contract below + `Idempotency-Key` UUID | 201 durable terminal pair | 202 pending replay; 409; 422; 429; 503 |
| `POST /conversations/{id}/messages/{user_message_id}/retry` | Empty object + a new `Idempotency-Key` UUID | 201 terminal existing user/new assistant pair | 202 pending replay; 404; 409; 429; 503 |

Title is trimmed nonblank 1..120 characters; language defaults to user preference
on creation. PATCH changes future reply language only; historical message language
is immutable. Pending turn blocks metadata mutation; deletion can cancel pending
work. Conversation reads/mutations return `ETag: "<version>"`; PATCH `If-Match`
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
Proposed caps: 100 unexpired conversations/user and 1,000 logical user turns per
conversation; return `storage_limit` when exceeded rather than silently deleting.

## Send and retry state machine

Send body is `{ "content": "How do I find permit information?" }`. No model,
role, history, citations, tool list or language override is accepted. Reply language
is the conversation preference snapshotted on its user turn; retry preserves it.

`Idempotency-Key` is required UUID. Bind key to conversation, operation/path and
canonical request body. Same key/body returns original pair without another charge;
same key/different operation or body =>409 `idempotency_conflict`. First send
allocates ordered user+assistant rows. Replay after commit returns 202 if assistant
pending or 200 if terminal, with `Idempotency-Replayed: true`. First successfully
reserved send/retry returns 201 once terminal even when provider failed, because
the durable attempt resource was created. Failures before reservation use normal
error statuses and create no messages. State is visible through message listings.

Turn result:

```json
{
  "user_message": {
    "id": "fded04d6-2d08-4c94-a024-74b49fd9e402",
    "sequence": 1,
    "role": "user",
    "status": "completed",
    "content": "How do I find permit information?",
    "language": "en",
    "parent_message_id": null,
    "answer_kind": null,
    "error_code": null,
    "citations": [],
    "created_at": "2026-10-13T10:01:00Z",
    "completed_at": "2026-10-13T10:01:00Z"
  },
  "assistant_message": {
    "id": "7d1494e4-ea6e-4915-993c-fb4505a12aa1",
    "sequence": 2,
    "role": "assistant",
    "status": "completed",
    "content": "I cannot verify this county's permit process from the approved information. Please use the county's reviewed service directory.",
    "language": "en",
    "parent_message_id": "fded04d6-2d08-4c94-a024-74b49fd9e402",
    "answer_kind": "abstention",
    "error_code": null,
    "citations": [],
    "created_at": "2026-10-13T10:01:00Z",
    "completed_at": "2026-10-13T10:01:02Z"
  },
  "request_id": "7df076dc-9d5c-4a55-95b2-9f2ec07e2ee8"
}
```

This is an illustrative abstention, not real county guidance or an approved contact.
Every Message has this common shape; pending assistant has null content/kind/error
and null completed_at; failed assistant has null content/kind, safe error_code,
empty citations and terminal completed_at. Valid codes include `provider_timeout`,
`provider_unavailable`, `provider_configuration_error`, `invalid_provider_output`,
`context_too_large`, `attempt_expired`. Refusal/abstention is a completed result,
not a failed request. Internal provider IDs, lease values, hashes and hidden
reasoning are absent from public Message objects.

One pending attempt per conversation. New sends are rejected with 409
`conversation_busy` during generation or `unresolved_turn` after a failed latest
turn. Retry targets only the latest unresolved user turn; 409 `turn_already_answered`
if completed, `retry_not_allowed` if not latest, or `conversation_busy` if pending.
An older failed assistant remains in history but does not enter prompts. Retries
use new attempt IDs and assistant sequence numbers without duplicating user text.
Deadline 30 s, lease 45 s; late results fail fencing. Cancellation/crash becomes
failed through recovery, within 60 s after lease expiry. Client must refresh state
before offering retry and never invent a new send key on a network timeout.

Citations are typed, server-validated references. MVP card citation:

```json
{
  "type": "catalogue",
  "source_id": "service-card-placeholder",
  "version": "reviewed-version-placeholder",
  "title": "Reviewed service information",
  "url": "https://example.invalid/official-service",
  "reviewed_at": "2026-10-13"
}
```

These placeholders never ship as approved evidence. Phase 4 adds type=document,
document/version/chunk IDs, page/section and official URL through a reviewed schema
extension. Browser cannot send citations. URL scheme/host must satisfy the source
registry; model-created links are rejected. No citation establishes legal authority.

## Operational and deferred contracts

`GET /health/live`: 200 when process runs; no dependency calls or secrets.
`GET /health/ready`: 200 only when settings, migrations and database are ready;
otherwise 503 with generic status. No paid provider call in health probes. External
provider availability is measured separately. These two paths are outside `/api/v1`.
P1-01 returns `{"status":"ok"}` for liveness. Readiness is absent (404) until
P1-02 can actually check database/migration state. P1-01 exposes only the local
schema at `/api/v1/openapi.json` and reserves the versioned router; it adds no domain
routes. Validation error details currently use `field: request` and `code: invalid`
to avoid echoing untrusted keys/input. Exact `Accept-Language: sw` selects fixed
Kiswahili errors; other values default to English. See the
[backend guide](../backend/README.md) for local CORS and logging limitations.
Metrics are restricted to operator network/authentication, never a public history API.

Document ingestion/search, tool invocation, account provisioning, public registration,
feedback, streaming and record-changing actions have no MVP endpoints. Later phases
must specify schemas/authz/errors before implementation. A server-internal tool
dispatcher is not permission to expose arbitrary tools through HTTP.
