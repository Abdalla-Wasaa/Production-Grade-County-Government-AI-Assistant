# P2-01 backend authentication contract

Status: contracts merged in PR #23; P2-01 backend is implemented behind explicit
enablement and exercised under isolated synthetic validation authorization. Machine-
policy/security acceptance remains blocked; no production approval is claimed. Frontend authentication, conversations, AI and live delivery are excluded.
[ADR 0002](DECISIONS/0002-invite-only-authentication.md) records the tradeoffs.

## Operator provisioning and recovery

An explicit identity operator CLI will use a separate restricted operator DB role;
never expose provisioning through HTTP or grant it to a JWT admin. Never auto-create
accounts during startup. Operators issue synthetic invitations with normalized
trimmed/lowercase email, fixed server-selected role, en/sw language, notice version,
operator pseudonym and a 24-hour expiry. Generate 32 random bytes using the OS CSPRNG;
store SHA-256 of the resulting secret, never its raw value. A restrictive 0600 file
in an ignored 0700 local directory is the sole token handoff output: no stdout,
command-line token argument, log, issue or artifact. Never overwrite a file or follow
a symlink. Do not copy coursework secrets or use live mail/real participant data.

An invitation URL may use a frontend fragment in the later UI; no query-string
secrets. Operators/users must not paste tokens into this repository or chat. HTTP
submits the secret only in the body to /activate. No delivery recipient verification
is implied by this synthetic protocol; a real pilot needs separately approved delivery.

Invitation purpose is server-stored activation or password_reset, never client-chosen.
Pending/expired/revoked/consumed invitations are not user states. Activation creates
an active user with a non-null password hash and notice acknowledgement. Duplicate
email or any invalid invitation has the same safe invitation_invalid response.
Reissuing revokes the previous outstanding invitation atomically before issuing a
new one; expired rows are revoked during that operation. Never reactivate a disabled
user through an invitation.

For synthetic recovery, an authenticated host operator explicitly selects an active
account and issues a password_reset invitation. The same /activate input consumes
it atomically, replaces the password, increments token_version and revokes all
sessions. Disabled accounts remain disabled; role/email never change via recovery.
This is operator-assisted reset only, not public account discovery or identity proof.
Tokens are purpose-bound and single-use. Purge expired/consumed/revoked invitation
secrets and recipient metadata within 24 hours after expiry; retain only minimal
nonsecret audit under its separate schedule. All issue/revoke/recovery operations require
a durable audit record. Operator credential/grant setup needs real PostgreSQL tests;
ordinary runtime cannot issue/revoke invitations or change user role/status.

## HTTP schemas and behavior

All paths below are under /api/v1/auth. Retain the exact login/refresh token response
and current-user shape in [API specification](API_SPECIFICATION.md). Pydantic rejects
unknown properties; never accept role, status, user_id, token_version or ownership
from a public request. All responses, including failures, use no-store, server request
IDs and the existing safe localized error envelope. Never echo input values.

| Method/path | Request and authorization | Success | Failure |
| --- | --- | --- | --- |
| GET /csrf | Approved Origin, or same-origin Referer fallback; existing refresh cookie if present | 200 csrf_token; HttpOnly scoped CSRF cookie | 403 origin; 429 abuse; 503 unavailable |
| POST /activate | Token, password, preferred_language en/sw, privacy_notice_version, privacy_notice_acknowledged=true; pre-session CSRF | 204; no access/refresh token; login separately | 400 invitation_invalid for unknown/expired/used/revoked/duplicate; 403 CSRF; 422 password/notice/fields; 429; 503 |
| POST /login | Email/password plus CSRF | 200 existing access token/user response and refresh cookie | Generic 401 for missing/disabled/wrong-password account; 403 CSRF; 422 shape; 429; 503 |
| POST /refresh | Empty object; refresh cookie and CSRF | 200 existing token response; rotated refresh cookie | 401 invalid/expired/replayed/revoked family; 403 CSRF; 429; 503 |
| POST /logout | Empty object; refresh cookie and CSRF | Idempotent 204 even absent/revoked; revoke family and clear cookies | 403 CSRF; 503 if required revocation cannot persist |
| POST /logout-all | Empty object; valid bearer AND CSRF | 204; revoke all families, increment token_version, clear current cookies | 401; 403; 503 |
| GET /me | Bearer and live active account/session | 200 existing user object | 401; 503 |
| GET /sessions | Bearer; own unexpired/unrevoked families only | 200 paginated items and next_cursor | 401; 422 cursor/limit; 503 |
| DELETE /sessions/{id} | Bearer and CSRF; owner predicate | 204 revoke family; clear cookies if current family | 401; 403 CSRF; 404 missing/other-user/already-revoked; 503 |

Activation token is a bounded base64url string; server decodes exact 32-byte entropy.
Passwords are not trimmed, normalized or truncated. Login accepts length 1..128;
activation/reset requires 12..128 Unicode characters and a versioned offline common/
compromised-password denylist. Reject invalid Unicode/NUL and preserve the 32 KiB body
cap. No live password-checking service or disclosure of passwords/hashes externally.
Notice version must match configured current version; reject stale/unacknowledged
notice before consuming the invitation. Server writes acknowledged_at; this is not
proof of a lawful processing basis. Locale defaults follow existing API rules.

Session item: id (UUID), created_at, expires_at, last_used_at (UTC), is_current.
No token hashes, user agent, IP, email or internal revocation detail. Use the existing
limit 1..100/default 20 and opaque cursor, ordered by created_at DESC/id DESC and
bound to the authenticated owner. Session lists are private and no-store.

There are no /register, public provisioning, password-recovery or dashboard routes.
Future recovery endpoints require separately reviewed delivery/verification contracts.

## Password and JWT controls

Use Argon2id with independent library-generated salt and encoded parameters. Initial
candidate: memory 64 MiB, iterations 3, parallelism 1; benchmark inside container CPU/
memory limits before finalizing. At least OWASP's 19 MiB/two iterations/parallelism
one floor. Bound expensive hashing in a worker thread with a per-worker capacity
limiter; budget all configured workers against container limits and reject overload
safely. Do not hold row locks while hashing. Unknown users verify a fixed dummy hash
with equivalent parameters; disabled/wrong-password accounts receive the same generic
denial. Rehash on successful login when policy changes, using a guarded update.
Constant-time primitives where applicable; no claim of perfect timing equivalence.

Use HS256 only with at least 32 random bytes of backend-only signing material,
separate CSRF and throttle-HMAC secrets. Require explicit configured issuer/audience;
never derive issuer/key URL/algorithm from attacker-controlled JWT fields. Validate
sub/sid/jti UUIDs, iat/exp types and interval, issuer, audience, signature, expiry and
nonnegative token_version. Access lifetime 900 seconds, bounded clock skew at most
30 seconds, plus absolute session-expiry validation with no extension by clock skew.
Check current DB role, active status, token_version and live session every request.
JWT role claims never confer permissions. Secret/key rotation must revoke affected
families or use an explicitly configured bounded verification-key window; no dynamic
JWKS lookup. Missing/malformed auth settings fail safely when auth is enabled;
liveness stays independent of PostgreSQL and no migrations run at startup.

## Refresh, CSRF and cookie lifecycle

Refresh families expire exactly seven days after login; rotations never extend it.
Store digests of 32-byte random refresh tokens. Keep consumed hashes through family
expiry for replay detection, then purge within 24 hours. No plaintext successor token
cache. Lock session family then token in a consistent order; recheck expiry/account
state; consume and create one successor in the same transaction. Set cookies only
after successful commit. A replay of any consumed token revokes the family and emits
audit in a committed transaction before returning 401. Transactions must not roll
back revocation simply because the HTTP request is rejected. Concurrent refresh
allows at most one successor; replay revokes it too. A lost response requires login,
not a replay exception. Later UI must serialize refresh across tabs, not just requests
within one tab. Logout-all, disable, password/role change and rotation use consistent
locks/version predicates so races cannot restore revoked authorization.

Preserve county_refresh and county_csrf: host-only, HttpOnly, Secure, SameSite=Strict,
Path=/api/v1/auth, Max-Age bounded by remaining relevant expiry. Clear with identical
path/attributes. Only explicit loopback synthetic HTTP may set Secure=false; defaults
remain secure. Do not share cookies across localhost and 127.0.0.1 origins.
Signed CSRF contains purpose, random nonce, expiry (proposed 30 minutes) and session
binding where present; compare cookie/header and signature safely. Reject absent/null/
foreign Origin, falling back to same-origin Referer only when Origin is absent. Use
configured origins, not untrusted Host/forwarded input. Check origin on GET /csrf too.

A pre-session CSRF token is needed for login/activation/logout without a valid family.
After login/refresh binds a family, fetch /csrf again before another unsafe request.
For revoked/absent families, obtain a fresh pre-session CSRF before idempotent logout.
CSRF lifetime never extends family lifetime. No wildcard credential CORS; prefer
same-origin Compose. Bearer-only reads do not authenticate from refresh cookies.

## Roles, throttling, audit and retention

citizen/staff/admin can authenticate, read their own identity/sessions and revoke
those sessions. No role grants cross-user access; no HTTP role-change or invitation
issuance permission exists. Future staff capabilities use an explicit deny-by-default
permission map and current-role dependency. Tests must distinguish 401, forbidden
capability 403 and concealed resource 404, including rejected role injection.

PostgreSQL owns counters keyed by HMAC of normalized submitted account/IP dimensions;
unknown accounts are counted identically. Five failed logins/account/15 minutes and
20/IP/15 minutes trigger 429 with bounded Retry-After/progressive delays, not permanent
account disable. Counters update atomically across workers; successful login must
not clear shared IP abuse history. Trust client addresses only from explicitly
configured proxy peers. Bound rows/cleanup and pre-hash admission; database failure
fails closed with safe 503. Initial additional limits: activation 5 failed attempts/IP/15 minutes, CSRF issuance
60/IP/minute, refresh 30/family/minute plus 60/IP/minute. Bound attacker-created
dimensions and apply global admission/resource caps before expensive work. These
synthetic-development defaults require abuse tests and measurement, not silent
threshold reductions to make tests pass.

Durable append-only auth audit records include pseudonymous actor/subject, event,
outcome, UTC time and generated request ID; allowlisted metadata only. Record issuance,
activation/reset, login success/denial/throttle, refresh/reuse, logout/revocation and
operator status/role changes. Never store bodies, credentials, raw tokens, raw IPs,
email or arbitrary exception strings. Mandatory audit failure rolls back successful
mutations and returns safe 503; denial/reuse changes and audit commit before errors.
Runtime may INSERT audit rows but not alter/delete them; controlled maintenance role
purges after the proposed 90 days, unless an approved incident hold applies.
No audit-table tamper-proof/WORM claim: DB administrators remain trusted.

## Planned configuration and verification

Planned backend-only settings: auth-enabled switch, JWT signing secret/issuer/audience,
CSRF secret, throttle-HMAC secret, explicit allowed browser origins, cookie Secure
flag, current privacy-notice version, offline password-blocklist path/version and
bounded hash concurrency. No production credentials or automatic .env discovery.
Secret values must use SecretStr and existing safe logging boundaries; local secret
files remain ignored. Exact variable names and tested operator CLI syntax belong
in the implementation PR, not invented runnable commands here.

Use real PostgreSQL 17 for empty upgrade from baseline, metadata/constraints, role
grants, duplicate activation and refresh races across separate sessions, audit
persistence and counter sharing. Test expired/consumed/revoked invitations, failed
password/claims/CSRF/origin checks, disabled users, current-role changes, session
ownership, recovery revocation and outage/recovery. Unit tests inject clock/RNG/
hasher interfaces. Measure hashing time, memory and overload handling. Preserve
safe live=200 independently of DB; ready requires reachability and latest revision.
Backend/unit/type/audit, PostgreSQL, Compose, repository/secret and unchanged frontend
checks all remain required. Evidence unavailable due to the exposure gate is pending,
never a pass. The nine handlers have isolated runtime evidence; current security-policy approval remains blocked.

## Exposure-impact boundary

The auth surface adds password hashing, token parsing and database writes to an
application previously serving only health probes. It adds authenticated PostgreSQL
operations; current libxml2/SQLite/zlib findings must be reconsidered without claiming
those libraries are or are not exploitable solely from their presence. No XML upload,
arbitrary SQL, archive processing, public ports, real data or live integration is
introduced. Non-root/read-only/capability/network controls remain required.

scripts/security_policy.py hashes app/migration/source/dependency/infra bytes. Changed
code cannot inherit the Phase 1 acceptance. Before running the changed app under an
exception, prepare focused changed-path/threat assessment, compatibility/dependency
and full built-image scans/KEV evidence, and request only the specific owner decision
required by policy. Building/scanning evidence is not permission to expose/run changed
services. Do not dispatch changed runtime integration CI before that gate is settled;
complete safe source/static work and report blocked runtime evidence. Do not update
the acceptance hash, renew/expand its scope or weaken the gate. Existing expiry:
23 October 2026, 23:59 EAT. Daily human CRITICAL review remains required; no production
approval is granted. Contract-only Markdown edits do not change the exposure hash.

Sources consulted for this design:
[OWASP password storage](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html),
[OWASP recovery](https://cheatsheetseries.owasp.org/cheatsheets/Forgot_Password_Cheat_Sheet.html),
[RFC 9700 rotation/replay guidance](https://www.rfc-editor.org/rfc/rfc9700.html).

Source preparation, environment/operator commands and actual verification status are
recorded in [operations](AUTHENTICATION_OPERATIONS.md) and the
[exposure assessment](P2_01_EXPOSURE_ASSESSMENT.md). These do not authorize execution.
