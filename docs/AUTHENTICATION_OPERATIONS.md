# P2-01 synthetic identity operations (restricted validation)

The owner authorized isolated synthetic validation, including bounded P2-01 fixes.
Backend, real PostgreSQL/operator and Nginx/Compose behavior has been exercised; see
the exact [validation/exposure record](P2_01_EXPOSURE_ASSESSMENT.md). This does not
authorize general deployment or automatically cover changed exposure. The current
exact owner decision and expiry are in the security policy records. Contracts remain
in [AUTHENTICATION.md](AUTHENTICATION.md); frontend authentication/history are now
implemented. Final clean-checkout verification is tracked in
[the Phase 2 acceptance candidate](PHASE_2_ACCEPTANCE.md).

## Explicit enablement and secrets

Auth defaults off (COUNTY_AUTH_ENABLED=false), preserving health-only startup.
Enabling it requires all settings below. No .env file is discovered automatically.
Use only generated synthetic secrets in ignored private files/environment, never
coursework environments, command-line URL/password arguments, logs or GitHub issues.

| Variable | Rule |
| --- | --- |
| COUNTY_ENVIRONMENT | development or test; existing requirement |
| COUNTY_DATABASE_URL | Restricted runtime URL; never the operator/migrator URL |
| COUNTY_AUTH_ENABLED | Explicit true to register the nine auth endpoints |
| COUNTY_AUTH_SIGNING_SECRET | Base64 encoding of at least 32 random bytes; HS256 only |
| COUNTY_AUTH_CSRF_SECRET | Independently generated base64 random bytes |
| COUNTY_AUTH_THROTTLE_SECRET | Third independent base64 random key for pseudonyms |
| COUNTY_AUTH_ISSUER / COUNTY_AUTH_AUDIENCE | Explicit nonblank expected values |
| COUNTY_AUTH_ORIGINS | JSON array of exact permitted browser origins, no wildcard/path |
| COUNTY_AUTH_COOKIE_SECURE | Defaults true; false only for explicit loopback synthetic HTTP |
| COUNTY_AUTH_PRIVACY_NOTICE_VERSION | Current synthetic notice version, maximum 64 characters |
| COUNTY_AUTH_PASSWORD_BLOCKLIST | Local ASCII file, one SHA-256 password digest per line, no raw passwords |
| COUNTY_AUTH_PASSWORD_BLOCKLIST_SHA256 | Exact reviewed file checksum; coverage/provenance must be approved before real pilot |
| COUNTY_AUTH_HASH_CONCURRENCY | Defaults one per worker, bounded 1..2; benchmark total worker memory/CPU |
| COUNTY_AUTH_TRUSTED_PROXY_ADDRESSES | JSON array of exact trusted peer addresses; otherwise forwarded headers ignored |
| COUNTY_AUTH_OPERATOR_DATABASE_URL | Operator/maintenance command only; separate restricted role and secret |
| COUNTY_MIGRATION_DATABASE_URL | Explicit maintenance migrations/grants only, never served by API |

Do not use a test fixture's one-entry blocklist as production password assurance.
The blocklist is offline and checksum-validated; no password/hash is sent to an online
service. The owned Compose test harness uses private leaf secret mounts and a test-only
launcher to set process configuration, never raw secrets in Docker Config.Env.
Normal Compose still defaults to auth off; no public deployment is added.

## Database roles and explicit migration

From backend/, after execution approval and synthetic disposable setup:

```bash
uv run --locked python -m app.db.migrate upgrade
uv run --locked python -m app.db.migrate check
```

Identity revisions are 0002_identity_accounts, 0003_identity_sessions and
0004_auth_controls, followed by 0005_conversation_persistence. P2-05 PR #28 adds
0006_privacy_lifecycle; final Phase 2 replay requires its reviewed merge and current
head verification. No startup migrations or seeded accounts/passwords. Backup/forward repair is preferred;
downgrades destroy identity/session data and are not normal recovery commands.

A trusted DB administrator must provision separate unprivileged LOGIN roles for
operator and maintenance tasks, with independently generated private SCRAM credentials.
No superuser/CREATEROLE/CREATEDB/replication/BYPASSRLS, inherited membership or ownership
of app objects. Do not reuse migration/runtime credentials or print password-bearing
SQL/errors. The grant CLI deliberately does not create roles or passwords:

```bash
uv run --locked python -m app.modules.identity.grants --runtime-role county_runtime --operator-role county_identity_operator --maintenance-role county_identity_maintenance
```

The command uses the migration URL and grants only the selected runtime/operator/
retention capabilities. Confirm effective permissions with the actual PostgreSQL
suite; additive grants do not erase historical broad grants. Any pre-existing broad
privilege must be investigated, not silently accepted. Runtime cannot update role/
status, issue invitations, alter/delete audits, run DDL or update alembic_version.
Operator can issue/revoke invitations, disable/change role and revoke sessions;
maintenance can purge expired identity/audit records after checking incident holds.
No application admin JWT grants host/operator credentials.

## Operator handoff, activation and recovery

After configuring the operator-only URL and the same auth keys/notice metadata,
from backend/ use an ignored private .local destination:

```bash
uv run --locked python -m app.modules.identity.operator invite --email pilot@example.invalid --role citizen --language en --operator synthetic-operator --output .local/identity/activation-token
uv run --locked python -m app.modules.identity.operator recover --email pilot@example.invalid --operator synthetic-operator --output .local/identity/reset-token
```

No raw token is printed; files are exclusive 0600 in an owned 0700 directory.
Never overwrite/reuse a file, follow symlinks or put a token in arguments/query strings.
No live email is sent. Deliver only inside the synthetic test workflow. A frontend
activation page is a later PR. The API receives token/password in JSON body, requires
pre-session CSRF plus approved Origin, language and current notice acknowledgement.
A client should read secrets into memory from its private input; never use shell
substitution to put tokens/passwords into curl arguments. Successful activation/reset
returns 204 without tokens. Then log in separately. Reset revokes existing sessions.

The same operator module supports revoke-invitation --id, disable --id and set-role
--id --role, always with --operator. These are audited explicit host operations,
not public endpoints. Reissuing invalidates old invitations; consumed/expired/revoked
secrets cannot activate. Disabled users cannot recover into active state.

After reviewed P2-05 merge, use the hold-aware privacy maintenance operator and the
merged `docs/PRIVACY_LIFECYCLE.md` runbook. The legacy identity purge command with
`--no-incident-hold` is deliberately refused; a caller assertion cannot bypass durable
holds. Explicitly enroll the dedicated maintenance principal and pin the existing
HMAC audit key via `--privacy-audit-key-file`, never by broadening runtime grants.

Eligible expired session families/invitations/counters are purged in bounded batches;
minimal audits retain the existing 90-day window, subject to active holds. The old
extra 24-hour post-expiry delay is removed. Daily 02:00 Nairobi and catch-up templates
are provided, but installation and operational evidence must be recorded; templates
alone are not an active scheduler. Synthetic targets are not a statutory schedule.

## Browser, key lifecycle and testing

The access JWT is 15 minutes and never persistently stored by the browser UI.
Refresh cookies are host-only/HttpOnly/SameSite=Strict on /api/v1/auth, Secure by
default, with a seven-day absolute family lifetime. Fetch /csrf before unsafe auth
operations and again after login binds a family. Missing/foreign Origin/Referer,
signature, expiry, binding or cookie/header mismatch fails closed. Replay revokes
an entire family, including a previously issued successor. Do not automatically
retry ambiguous refreshes; the frontend must serialize refresh across tabs.

Key rotation requires explicitly managed new secrets and revocation/version updates
for affected sessions; never accept token-supplied algorithms/JWKS locations. Source
implements one active signing key, not federation or unattended rotation. CSRF-key
rotation invalidates CSRF/cursors; clients must obtain fresh state. No key material
belongs in Vite/browser config. IP/account throttle keys and audit identities are
pseudonymous but can still be linkable; they are not a privacy exemption. With P2-05
privacy enrollment, the HMAC key is fingerprint-pinned for holds/audit correlation;
rotation requires a separately reviewed binding migration and fails closed on mismatch.

Within the approved isolated synthetic validation scope:

```bash
uv run --locked pytest -q -m "not integration"
uv run --locked pytest -q -m integration
uv run --locked python -m app.modules.identity.benchmark
```

Integration requires COUNTY_TEST_ADMIN_URL pointing to loopback postgres and
COUNTY_TEST_DISPOSABLE=YES; only fixture-owned random databases/roles may be removed.
Run the benchmark inside the actual bounded container and record Python/CPU/memory/
worker settings, duration and peak RSS; source parameters are not measurements.
Existing Compose/browser/tooling checks remain required. Do not dispatch changed
runtime CI until its security gate is resolved; a pending test is never a pass.
