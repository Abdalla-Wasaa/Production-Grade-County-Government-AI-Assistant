# ADR 0002: Invite-only accounts and revocable rotating sessions

Date: 2026-10-17. Status: owner-approved direction; contract review pending.
This ADR specifies P2-01; no authentication functionality is implemented by it.
Implementation starts from reviewed, merged contracts on
feat/p2-01-account-authentication. No PR is merged without owner review.

## Context

Phase 1 closed at c49998ff2c8ec371085e2c1a5341ba60af4f2ec1. The owner authorized
backend-first P2-01, fixed citizen/staff/admin roles, no public registration,
operator-assisted synthetic activation/recovery and no live email. Phase 0 already
specifies 15-minute access JWTs, seven-day absolute refresh families and browser
CSRF/cookie contracts. New activation/session APIs need reviewable contracts before
implementation. [Authentication specification](../AUTHENTICATION.md) is normative
for this milestone alongside the existing API/security/database documents.

## Decision

- Keep one constrained role on users; no roles/permissions join tables or dashboard.
  Derive current role and account/session validity from PostgreSQL on every protected
  request. Admin never implicitly obtains another user's sessions or conversations.
- Store only digests of random 256-bit invitation/refresh secrets. Activation creates
  a user atomically; pending invitations do not require nullable password hashes.
- Use Argon2id and bounded hashing work; measure parameters in the actual container
  limits before claiming performance. No password normalization/truncation.
- Issue explicitly validated HS256 access JWTs with separate high-entropy signing
  and CSRF secrets. Preserve the 900-second token response and claims contract.
- Keep consumed refresh hashes until absolute family expiry to detect replay. Lock
  the family before rotation; replay revokes the family in a committed transaction.
  No replay grace window, automatic ambiguous-refresh retry or indefinite renewal.
- Keep access tokens in browser memory in the later frontend PR. Refresh uses scoped
  HttpOnly cookies, signed CSRF and explicit Origin/Referer checks. SameSite does not
  replace CSRF validation. No change to same-origin proxy architecture.
- Keep throttles and durable minimal audit in PostgreSQL, not per-worker memory.
  Authentication mutations fail safely if mandatory audit persistence is unavailable.
- Operator recovery issues a different-purpose, one-time reset invitation consumed
  through the activation contract. No public recovery/registration endpoint, live
  delivery or reusable temporary password. No automatic login after activation/reset.

## Tradeoffs and alternatives

Live session lookup trades a DB read for immediate revocation; JWTs are not an
offline authorization source. Strict replay handling can require login after a lost
refresh response or unsynchronized tabs; the frontend must serialize across tabs.
Fixed roles avoid a permission-management subsystem. HS256 is bounded to the single
backend trust domain; federation/SSO requires a new key/trust decision. No blanket
OAuth authorization-server compliance is claimed. PostgreSQL counters avoid another
service but require bounded indexes, contention and cleanup tests.

Public recovery, multi-role assignment, staff SSO/MFA, external delivery and admin
UIs remain outside P2-01. Operator trust is distinct from an application's admin role.

## Security gate and consequences

The existing 115 HIGH/3 CRITICAL acceptance is bound to Phase 1 exposure. Application,
migration, lock or infrastructure edits change the computed exposure hash in
scripts/security_policy.py. Do not update the stored hash or claim existing approval
covers new code. Source-level work may be prepared after contract merge, but running
changed code under the exception or obtaining green integration security gates needs
focused exposure assessment, current scans and the owner decision required by policy.
No renewal/expansion or expiry extension is authorized. The existing expiry remains
23 October 2026, 23:59 EAT; production remains prohibited.

Acceptance requires real PostgreSQL race/replay/permission tests, safe errors and
logging, measured hashing limits, complete scans, all seven unchanged CI contexts
and owner review. See [roadmap](../ROADMAP.md). No tests are claimed by this ADR.
