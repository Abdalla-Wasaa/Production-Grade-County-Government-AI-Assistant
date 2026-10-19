# Synthetic privacy lifecycle and operator runbook

Status: P2-05 engineering policy approved on 19 October 2026. Two explicitly
authorized synthetic test attempts are recorded in [the exposure assessment](P2_05_EXPOSURE_ASSESSMENT.md).
The latest account-deletion query correction still needs fresh runtime authorization;
installation and changed-exposure security acceptance remain pending. Do not execute
these commands against that corrected source until its checkpoint is cleared. This is a fictional local environment, not legal advice,
a county records schedule, a production service or authority to use real data.

## Policy and scope

Conversation expiry stays `min(created_at + 90 days, last accepted new user message
+ 30 days)`. Reads, renames, identical message retries, holds and deletion requests
never extend it. Expired history remains immediately invisible, including held
records. No expired/deleted conversation is restored to active history.

The existing authenticated owner-only conversation DELETE returns 204 only after
actual removal. An owned, live held conversation returns fixed safe 409
`deletion_restricted`; it remains stored, no hold reason is disclosed, and the UI
uses a fixed bilingual restriction message. Unknown, other-user and expired IDs
still return 404. A 409 is not a completed or queued deletion. Contact the authorized
operator to record the request/resolve a restriction; no public admin API is added.

Account deletion uses the verified operator API below, not public registration,
an admin dashboard, a citizen-supplied role, or an unverified email link. Acceptance
atomically disables the account, increments its token version, revokes every
session and records a mandatory audit event/request. An audit failure rolls all
of this back. The operator must verify identity and authority through the synthetic
case process before supplying `--verified`; software does not certify that human step.

Requests retain their original acknowledgement and completion dates. Acknowledgement
is returned after commit; target is two working days from documented receipt.
Working days here are Monday-Friday, with no claim of an approved statutory holiday
calendar. Eligible completion target is seven calendar days after acceptance.
`--received-at` records an earlier actual receipt if relevant; never backdate or
reset targets on retry. These are development service targets, not legal deadlines.
Held requests show `held` and their original target; they are not falsely marked
completed. Review the hold/deferral with the requester, without exposing case details.

## Authorization and secrets

The operator API is `python -m app.modules.privacy.operator COMMAND`. It has no HTTP
administrator surface. PostgreSQL `session_user` is the authenticated principal;
caller-supplied operator names and JWT citizen/staff/admin roles confer no rights.
SET ROLE impersonation fails closed. `privacy_operators` starts empty. The reviewed
DB owner must explicitly enroll dedicated, non-owner, non-inheriting roles.

The existing identity grant command adds privacy capabilities only when explicitly
passed `--privacy-audit-key-file`. The operator role receives hold/request rights;
the separate maintenance role receives batch-completion rights but cannot issue or
release holds. Runtime receives only safe boolean-check functions, not privacy
control-table DML or account deletion. Maintenance has UPDATE only on the
updated_at column of user/conversation parents to satisfy PostgreSQL row-lock
privileges; it cannot edit passwords, roles, status, content or expiry. The DB owner can disable an operator's
registry entry; the CLI then rejects new operations. No automatic enrollment runs
at migration or application startup.

Configure private files, outside Git:

```text
COUNTY_PRIVACY_DATABASE_URL_FILE=/absolute/private/path/to/role-database-url
COUNTY_PRIVACY_AUDIT_KEY_FILE=/absolute/private/path/to/auth-throttle-key
```

The first file contains that role's PostgreSQL URL. The second contains the existing
base64 auth throttle/HMAC secret, never the JWT signing or CSRF secret. Do not put
values in CLI arguments, logs, reports or public Vite configuration. Secret files
must be regular, not symlinks or group/world-writable; host files should be 0600
under owned 0700 directories. Parent directories are also checked for symlinks.
No environment file is auto-discovered by the command.

After explicit runtime authorization, the DB owner can use the existing grant
command with `--runtime-role`, `--operator-role`, `--maintenance-role` and the
additional private `--privacy-audit-key-file` option. Connection credentials use
the existing migration-secret mechanism. This enrollment pins the decoded key's
SHA-256 fingerprint so holds protect existing pseudonymous audits. A wrong key
fails closed. Once enrolled, changing the auth HMAC key without migrating hold
bindings makes auth return safe 503; plan that rotation separately. JWT/CSRF keys
are independent. Do not change the fingerprint to get around this guard.

DB owner/superuser access remains trusted: it can alter schema/guards and is not
made tamper-proof by this feature. Ordinary deletion paths, including cascades,
are checked by fixed-search-path SECURITY DEFINER triggers. Functions have no
public EXECUTE grant. No role may create arbitrary functions or bypass a hold as
part of normal maintenance.

## Operator command contracts

All identifiers/references are UUIDs for synthetic cases, not names, messages,
email addresses or free-form legal documents. Outputs contain only operation IDs,
statuses, dates or counts. Never redirect output to a public log sink.

| Command | Required options | Effect |
| --- | --- | --- |
| `hold-create` | `--id`, `--scope account|conversation`, `--target`, `--reason incident|records|review`, `--case` | Idempotent creation for the exact resource; reason and case reference immutable |
| `holds-due` | none | Return at most 100 overdue hold IDs/deadlines for authorized review; review then repeat until clear |
| `hold-review` | `--id`, `--case` | Explicit review; next deadline is 30 days later |
| `hold-release` | `--id`, `--case` | Explicit authorized release; identical repeats are safe |
| `request-delete` | `--id`, `--target` user UUID, `--case`, `--verified`; optional `--received-at` | Accept verified account request and immediately disable/revoke access |
| `status` | `--id` request UUID | Read accepted/held/completed status and service dates |
| `tick` | optional `--limit` 1..100 | Evaluate daily/catch-up work; scheduler principal only |
| `purge` | optional `--limit` 1..100 | Explicit bounded pass regardless of daily clock; scheduler principal only |

A repeated request UUID with another target or verification reference is rejected.
A second key for the same pending account returns its canonical request; it never
revokes/retimes repeatedly. After completed deletion, the original key still returns
the completed request. Request state is retained for 90 days after completion,
matching the existing minimal audit retention proposal, not forever.

Holds carry scope, fixed reason code, case reference, authenticated issuer digest,
creation/review/release times, reviewer/releaser digest and review/release references.
They are reviewed every 30 days. These privacy-hold reviews are distinct from the
daily human CRITICAL vulnerability review; synthetic tests complete neither human obligation. Overdue review alerts and remains active; neither
scheduler nor clock expiry releases it. Account holds protect all associated data;
conversation holds preserve that conversation/messages and user-correlated audit
records. Because existing conversation audits identify a user rather than a specific
conversation, audit preservation is conservatively per affected user. Releasing a
hold does not renew conversation expiry or re-enable a disabled account.

When account deletion is held, unheld conversations can be removed but the disabled
account remains while any owned hold is active. After release, the next pass completes
eligible deletion. Invitations for the account, sessions and refresh hashes are
removed with the account; domain FKs cascade conversations/messages. Released hold
metadata survives as minimal UUID/case/audit evidence for 90 days, without content.

## Scheduling and the conditional 24-hour bound

Daily maintenance is targeted at **02:00 Africa/Nairobi**. The supplied user-systemd
timer invokes `tick` every 15 minutes and after boot, with persistent catch-up.
The command records the last successful daily pass in PostgreSQL. A missed daily
pass is due immediately; pending account requests also trigger work. Independently,
eligible records aged 23 hours trigger a safety catch-up before the 24-hour bound.

Each pass uses one nonblocking database advisory maintenance lock, account-first
row locks and bounded batches. Concurrent invocations return `busy` without claiming
work. A remaining eligible backlog does not mark the daily run complete and causes
attention; subsequent ticks catch up. Identity retention now purges after expiry,
not expiry plus another 24 hours. Consumed refresh hashes remain through family
expiry. Account-held identities and held audit subjects are excluded. Operator operations, guard checks and audit writes are transactional.

**Operating assumptions to validate before enabling the timer:** accurate UTC clocks;
PostgreSQL and the authorized runner continuously available; no gap exceeding
16 minutes between ticks; an eligible backlog that clears in a pass of at most
100 parent resources/category (at most 100 conversation parents), with associated
cascade work finishing within five minutes. Under those assumptions the 23-hour
catch-up threshold plus tick delay and execution stays below 24 hours. This is not
an unconditional guarantee during prolonged outages or overload.

A batch that cannot clear, missed operating assumptions, or failure of that capacity
measurement means the bound is unproven: stop and obtain the owner's policy/capacity
decision, rather than increasing limits or silently relaxing the target. Tests of
intentional outages/backlog must report that loss of guarantee. `deadline_breached`
is retained in output/audit when a pass sees eligible records already 24 hours old,
even if that pass subsequently clears them. Holds are an explicit eligibility
exception, not an overdue record to delete.

The templates are in `infra/maintenance/`. Before authorized installation, replace
the example checkout/venv paths with this checkout's absolute paths. Create a private
user service environment file containing only the two secret-file paths. Run under
the dedicated host operator, inspect the rendered unit and test a manual pass before
enabling the timer. Never run as a database owner/superuser. No timer was installed
or started during source preparation.

Exit 0 means completed/idle/busy, with explicit status distinguishing each. Exit 2
means overdue reviews/requests, backlog or a missed purge bound requiring attention.
Exit 1 means failed configuration, authorization, database or audit operation, with
a generic message. The supplied OnFailure unit writes a fixed error to the local
journal; it sends no external messages. Review `systemctl --user status`, timer
last/next-run status and the safe JSON results. A staffed alert channel is a separate
pre-pilot requirement; an unattended journal is not a production monitoring claim.

The legacy identity `purge --no-incident-hold` path now refuses to run. A human flag
is not a substitute for durable hold checks. Do not use direct SQL to bypass the
new maintenance API or claim a manual review completed automatically.

## Failure, recovery and audit boundaries

On a failed transaction, retry with the same request/hold IDs. No success JSON is
printed until commit. Audit failure rolls back deletion, revocation, request state
and ledger writes together. Do not catch an error and mark a request complete.
After service recovery, run an authorized tick and inspect backlog/deadline/hold
flags before claiming target compliance. `held` requests require authorized review;
never release a hold to make a test, timer or dashboard green.

Runtime cannot update/delete audit records. Mandatory audit records contain bounded
pseudonymous actors/subjects, fixed event/outcome and a correlation UUID; no bodies,
raw email/IP, passwords or tokens. Hold and accepted-request triggers also audit
low-level writes so the CLI cannot announce unaudited changes. The existing HMAC
key links user audit subjects; actual database principals are hashed for operator
attribution. Pseudonyms are still linkable data, not anonymous or tamper-proof records.

The deletion ledger contains object kind/UUID/deletion time only, through the
existing 30-day backup window plus seven days (37 days). Live deletion is not
instant erasure of every backup. Before any restore is exposed, preserve the current
ledger independently of that backup, restore into isolation and replay deletions
and expiry/revocation checks. No backup service, public export or production restore
approval is introduced here. Until a proper preservation/replay drill is evidenced,
no production recovery assurance is claimed.

Downgrade refuses while active/recent holds, unfinished/recent deletion requests or
unexpired ledger records need safeguards. A pristine upgrade/downgrade is testable;
do not erase privacy evidence or force a downgrade to remove these checks.

## Prepared validation and Phase 2 handover

Focused tests live in `backend/tests/test_privacy_contracts.py`,
`backend/tests/integration/test_privacy.py` and the frontend held-delete client case.
They cover clock boundaries, catch-up/backlog, concurrency, direct-cascade guards,
operator/cross-user denial, holds/review/release, immediate revocation, idempotent
account deletion, audit rollback, fingerprint mismatch and guarded migrations.
See the exposure assessment for actual passing/failing results and the exact next
checkpoint; no later correction is automatically covered by earlier testing.

P2-06 must reuse valid prior authentication/history evidence, add actual P2-05 test
and capacity/timer/recovery results, perform the required clean-checkout replay,
verify seven hosted checks and fresh scans, and record real human CRITICAL-review
and manual language/accessibility status. Do not close issue #22 or Phase 2 based
only on a closed tracker/checked box. No provider dispatch or Phase 3 start follows
from this work.
