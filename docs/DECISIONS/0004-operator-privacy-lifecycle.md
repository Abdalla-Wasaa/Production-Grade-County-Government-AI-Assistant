# ADR 0004: operator-managed synthetic privacy lifecycle

Status: engineering policy approved by the owner, 19 October 2026. Implementation
source prepared; runtime/security acceptance is a separate pending decision.

Retain min(30 days since last accepted new user turn, 90 days from creation).
Use the existing host-operator workflow rather than a new public admin service or
JWT admin privilege. Explicitly enrolled database roles separate hold/request issuance
from unattended maintenance. Parameterized SQL and existing sessions/audit infrastructure
are reused; no new package, provider or payment integration is introduced.

Durable holds use fixed reasons/private case references, actual DB-principal
attribution, mandatory audits, 30-day review and explicit release. Overdue reviews
alert and never erase the hold. Account requests immediately disable/revoke access;
unheld records can be deleted while held material and the disabled root remain.
DELETE cannot report 204 for retained held content: the approved hold behavior is
409 deletion_restricted. This is the focused amendment to the existing API.

Database deletion guards protect parent cascades and correlated audits as defense
against a bypassed application check. The schema owner remains trusted and can
alter controls; this is not WORM protection or proof of actual human verification.
The existing auth HMAC fingerprint is pinned so operator holds refer to existing
audits without giving maintenance a JWT signing key. Rotation requires a reviewed
binding migration; a mismatch fails closed, trading availability for privacy safety.

The daily 02:00 Nairobi target plus 15-minute boot/persistent checks, a 23-hour safety
threshold, bounded batches and backlog/deadline alerts provide a conditional sub-24h
purge bound under the runbook's continuously available/capacity assumptions. Outage
or overload does not magically satisfy the target: report it and seek a policy or
capacity decision. A new background framework/cloud scheduler is unnecessary here.

Raw content stays only in domain tables. Minimal released control/audit metadata
uses the existing 90-day audit window; the deletion ledger uses backup 30+7 days.
Live deletion does not prove backup erasure; preserve/replay the ledger before an
isolated restore can be exposed. Production and real records authority remain gated.

See [the runbook](../PRIVACY_LIFECYCLE.md), [database design](../DATABASE_DESIGN.md)
and [API contract](../API_SPECIFICATION.md) for exact behavior and limitations.
