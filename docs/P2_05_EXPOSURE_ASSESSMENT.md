# P2-05 source checkpoint and focused exposure assessment

Status: authorized/reused functional coverage is complete; **separate P2-05 security-record approval pending**.
Intermediate checkpoints below are retained chronologically; the final section is current.
Implementation and prepared-test commit: `969535e` (documentation-only follow-up
commits do not change the exposure). Branch: `feat/p2-05-privacy-lifecycle`.
Base: merged P2-04 PR #27, `a7902700e10dcd6fc71ebf582ba84fada1d93254`.
This document records exact runtime evidence and pending decisions. It is not a
security acceptance or a human CRITICAL review.

## Exact exposure and dependency delta

Previous approved P2-04 exposure:
`2c8e739185e6f0fc748a4594657ab09978e589563f3464714a7cd97f6aa04996`.

Prepared P2-05 exposure:
`c7fad27da4122a52b07efb3fd1efa6fcbfbb2c3f884f24b0c7c9257853626e90`.

Calculated by the unchanged `scripts/security_policy.py:exposure_sha256` over
tracked/untracked policy-selected source, migrations, infrastructure and locks.
No package manifest, lockfile, image pin, Compose network or published port changed.
No dependency was introduced, removed or upgraded. Complete image inventories:

| Image | Packages | Inventory SHA-256 |
| --- | ---: | --- |
| Web | 21 | e9d19af8839b51cd311f6b527994b6cc624ee2b0491513c293f6fefa6cb60443 |
| Backend | 119 | 7c9d236e62e9b96b9dfe7ca03dd92b1d999c6bacfb7fb8f67949a9790d88274e |
| PostgreSQL | 144 | f0ff6951e8f3157a9f0e6d15387c68b6e4e591afd21d2d0da972c122ed1ad288 |

Immutable image IDs, complete-inventory comparison, raw report hashes, KEV snapshot
and exact occurrence deltas belong in [scan evidence](security/p2-05/scan-summary.json)
and [the image manifest](security/p2-05/image-manifest.json). These are observations,
not approved baseline or inventory-policy updates. Raw local reports are retained at
`/tmp/county-p205-image-evidence/scans/`; they are not application runtime evidence.

## New attack surface and safeguards

- Migration `0006_privacy_lifecycle` adds five control tables, database delete guards,
  mandatory hold/request/deletion audits and tightly scoped SECURITY DEFINER functions.
  The schema owner remains trusted; the controls are not immutable records storage.
- An explicitly enrolled PostgreSQL operator can issue/review/release holds and accept
  verified account requests. An operator assertion is not proof that actual identity
  verification happened. Compromise of that credential can disable accounts or misuse
  holds; reviewed enrollment, private secret files and synthetic isolation remain essential.
- A separate maintenance principal gains narrowly scoped reads, parent row-lock updates
  and physical deletion rights. It cannot issue/release holds, change passwords/content
  or sign JWTs. Compromise can delete eligible unheld synthetic data; database guards
  and transactional audit reduce, but do not eliminate, that risk.
- Existing auth HMAC correlation is fingerprint-pinned. Maintenance needs that key,
  increasing its confidentiality footprint, but receives neither JWT nor CSRF secrets.
  Mismatch fails closed; rotation needs a separately reviewed binding migration.
- The timer templates introduce a host maintenance entry point, with secret paths only,
  five-minute execution deadline, bounded batches, nonblocking serialization, daily
  02:00 Nairobi target and 15-minute catch-up ticks. No timer was installed or executed.
  Failures/backlog/overdue holds are visible; a local journal alert is not a staffed
  operational response. Capacity and scheduling assumptions remain unverified.
- Existing authenticated owner DELETE gains fixed `409 deletion_restricted`; other-user
  and expired IDs remain 404. Fixed English/Kiswahili UI errors disclose no hold reason.
  No public operator endpoint, external integration or additional listener is added.
- Audit/control metadata uses bounded identifiers and pseudonyms, never message bodies
  or credentials. Released controls retain evidence for 90 days and the minimal deletion
  ledger for 37 days. Backup erasure/replay is an operational obligation, not a new
  backup implementation or a claim of statutory authority.

Source review found a bounded-queue starvation issue: fully held requests could block
later eligible requests. The selector now excludes fully blocked requests until release
or eligible child data appears; a dedicated PostgreSQL regression case is prepared.
This correction has not been executed and is included in the exact exposure above.

## Scanner findings and inherited CRITICAL assessments

| Image | HIGH | CRITICAL | Scanner-reported available fixes |
| --- | ---: | ---: | ---: |
| Backend | 44 | 0 | 0 |
| PostgreSQL | 71 | 3 | 0 |
| Web | 0 | 0 | 0 |
| Total | 115 | 3 | 0 |

All 118 HIGH/CRITICAL package/CVE occurrences are inherited OS findings: zero added,
removed or severity/fix/status changes against the accepted occurrence baseline.
No matching CVE appears in the retrieved KEV snapshot. These are scanner observations;
absence of new advisories does not prove new code is vulnerability-free or establish
exploitability. Dependency audits found zero advisories for the exact backend/dev,
repository-tool and frontend lock inventories. CVE-2026-77214 remains absent from web.

| Existing PostgreSQL CRITICAL | Existing exposure assessment; P2-05 delta |
| --- | --- |
| CVE-2025-7458, SQLite 3.40.1-2+deb12u2 | Crafted SQLite SQL prerequisite; no demonstrated current API exploit. P2-05 adds PostgreSQL parameterized operations, not SQLite parsing. |
| CVE-2026-6653, libxml2 2.9.14+dfsg-1.3~deb12u6 | Authenticated PostgreSQL SQL/XML is a plausible path after SQL/DB compromise; no reproduced exploit. Privileged maintenance is an expanded credential exposure, but adds no XML-processing operation or arbitrary-SQL API. |
| CVE-2023-45853, zlib 1:1.2.13.dfsg-1 | Existing Debian assessment says affected MiniZip code is excluded from these binaries. Finding remains recorded; no archive-upload/extraction path is added. |

Daily human review of all three remains required and **unconfirmed**. Engineering
approval, scan success and synthetic test authorization must not be recorded as that
review. No independently reproduced exploit is claimed; credential compromise and
unreviewed new logic remain material risks even with unchanged scanner totals.

## Completed static evidence and prepared runtime work

Completed: Ruff lint/format, strict Mypy with `backend/pyproject.toml`, TypeScript,
ESLint, Prettier, frontend image production build, repository document/config checks,
whitespace checks, Gitleaks and systemd calendar-expression parsing. Image builds/scans
inspect packaged source and dependencies; they do not run changed application code.
The systemd units have not been installed or operationally verified.

Prepared, **not collected or run**:

- 22 backend policy/schema/secret-handling cases in `test_privacy_contracts.py`.
- 27 real-PostgreSQL lifecycle cases in `integration/test_privacy.py`, covering expiry,
  missed runs, bounded backlog, nonblocking concurrency, authorization/holds, session
  revocation, idempotency, held queue fairness, direct cascade guards, audit rollback,
  HMAC mismatch and guarded upgrade/downgrade.
- One frontend client regression for held-delete handling; existing backend/auth/history
  suites require appropriate regression replay because migration/grants/HTTP checks changed.
- Timer/capacity/recovery evidence: validate disposable execution, deadlines, failure
  visibility and the runbook's conditional sub-24-hour bound before enabling a scheduler.

After explicit authorization, execute backend Pytest from `backend/` using the locked
Python environment, first focused contracts, then real-PG tests with the existing
`COUNTY_TEST_ADMIN_URL` loopback disposable setup and `COUNTY_TEST_DISPOSABLE=YES`.
Use JUnit reports and run the affected frontend client test. Full relevant regression,
Compose and hosted checks follow only within the authorization actually granted.
Do not claim old migration/auth results verify revision 0006 or these changed paths.

## Fail-closed checkpoint and exact decision

The unchanged CI policy reports `Application/infrastructure exposure changed; owner
review required`. The complete image scan produces all three reports but rejects
current acceptance for this new exposure; it does not treat missing evidence as clean.
All seven checks, scanning, ruleset and invalidation triggers remain unchanged.
No security baseline, inventory, acceptance or historical snapshot was modified.

Request **isolated synthetic runtime-testing authorization only** for implementation
`969535e` and exposure `c7fad27da4122a52b07efb3fd1efa6fcbfbb2c3f884f24b0c7c9257853626e90`,
including focused backend/PostgreSQL, affected auth/history/frontend regressions and
operational maintenance/capacity verification. Stop before executing any subsequent
correction that changes exposure, as required by the current authorization procedure.

A separately approved, exact security-record decision is still needed before publishing
and normal CI under a changed-exposure exception. The P2-04 acceptance is not inherited.
Its expiry stays **23 October 2026, 23:59 EAT**, with no renewal/expansion, production,
real citizen/county data or automatic merge. The runbook's availability/capacity bound
must be tested; if it cannot be met, stop for the owner's policy/capacity decision.

Issues #21/#22 are open because source preparation is not acceptance. P2-06 still
requires P2-05 runtime evidence and merge, a clean-checkout replay, seven hosted checks,
fresh final audits/scans, operational handover and explicit human-review status.

## Authorized runtime attempt and correction checkpoint — 19 October 2026

The owner subsequently authorized synthetic testing of final documentation commit
`f3fbf77c8986a2490d1f758b4df7dd8432fe500b`, with the exact exposure above. This supersedes
only the earlier pending runtime status for that exposure; no acceptance update,
push, PR or human CRITICAL review was granted. Actual sanitized evidence is in
[runtime summary](security/p2-05/runtime-attempt-summary.json).

| Executed suite, approved application exposure | Passed | Failed |
| --- | ---: | ---: |
| Privacy backend contracts | 22 | 0 |
| Privacy PostgreSQL | 14 | 13 |
| Frontend client, including the new held-delete case | 11 | 0 |
| Existing auth/conversation/PostgreSQL integration | 49 | 2 |
| Existing auth/conversation/logging unit regressions | 49 | 0 |

Initial test-only fixture defects (a missing synthetic URL password and an unimported
transitive auth fixture) were corrected and rerun without changing exposure. Failures
above are actual application failures, not suppressed/skipped cases. The two confirmed
root causes are an unnecessary child-row lock without an operator UPDATE grant, and
PostgreSQL resolving `OLD.status` on non-user table records in the shared guard.

Prepared correction commit `a3b5d808d0ced39c1fa90c898f565eca86ab85a8` removes only the
redundant child lock (account-first locking/DB guards remain) and nests users-only
record access in a separate trigger statement. No permission is broadened or hold
check removed. Ruff, formatting and strict Mypy pass. A new 100-parent/500-message
capacity case is prepared; the focused PostgreSQL suite now contains 28 cases.

Corrected exposure, **not executed**:
`13e5dbf0a8e35918ef4c61d4787f544d08c0c3459d382cc3a4825b9876c688c1`.

Stop before executing that corrected source. Request isolated synthetic authorization
for its 28 PostgreSQL cases, affected regression failures and maintenance/capacity/
recovery verification. No corrected passing result, capacity measurement, scheduler
installation or sub-24h operational guarantee is claimed. Existing passing unrelated
unit/frontend evidence can be reused; a pristine migration case passed, but this does
not validate the corrected delete paths.

No manifest/lock/image-pin or security-policy/acceptance/snapshot changes occurred.
The previous fresh image scans remain evidence for unchanged dependency inventories
and the authorized pre-correction images, **not a scan of a corrected rebuilt image**.
Residual observed findings remain 115 HIGH/3 CRITICAL, no reported fixes or KEV matches;
no new dependency or scanner finding is inferred from these two source-only fixes.
Do not mistake that for proof of vulnerability-free code. Any final image rebuild
must retain fresh complete scans before review. Daily human review remains unconfirmed
and expiry remains 23 October 2026, 23:59 EAT.

Disposable PostgreSQL used fresh databases/roles and tmpfs storage. Zero test databases
or roles remained before removing the owned container and private password file.
Unrelated containers/coursework were untouched. P2-06 still needs passing P2-05
runtime/capacity evidence, separately approved security records, reviewed merge,
clean-checkout reproduction, seven hosted checks and operational/manual review status.

## Corrected-source authorized validation — 19 October 2026

The owner authorized `095aa6594463a4ca7e645935f359c06cf67483f3` / exposure
`13e5dbf0a8e35918ef4c61d4787f544d08c0c3459d382cc3a4825b9876c688c1`.
Actual [corrected runtime evidence](security/p2-05/corrected-runtime-summary.json):
privacy PostgreSQL **25 passed / 3 failed**, selected existing regressions **14/14 passed**
(including both formerly failing cases, ownership/expired concealment, revocation,
authorization and outage/recovery). Existing unaffected 22 contract, 49 unit and
11 frontend results are reused; they were not unnecessarily rerun.

The three remaining account-completion failures share one root cause: SQLAlchemy's
`exists().where(...)` emits `SELECT *`, which exceeds maintenance's column-level
conversation SELECT grant. Prepared source correction `50f4724` explicitly selects
`Conversation.id`; no privilege or hold protection changes. Test-only follow-up
`a21cb89` strengthens physical-deletion audit rollback to require the injected
`synthetic audit failure`, rather than accepting any DBAPIError. Its earlier pass
must not be claimed as proof that the intended audit fault was reached.

New exposure, **not executed**:
`e363174d230cc0732e221d1bae835b0bc95bb6cc0921ef029c34b7a589ea797d`.
Stop before executing it. The minimum next authorization is synthetic validation
of the three account-completion failures plus strengthened physical-deletion rollback;
reuse unaffected results. A security-record approval is premature until those pass.

### Measured capacity, recovery and limits

The capacity case passed: 100 expired conversation parents / 500 synthetic messages
were physically deleted with 100 ledger entries, no eligible backlog and no deadline
breach. Maintenance invocation measured **0.204737771 seconds** on this local disposable
PostgreSQL instance; whole case including setup/teardown was 2.050 seconds.
Missed-run catch-up/repeated idle, bounded batch backlog, nonblocking concurrent
maintenance and the 23-hour urgency path all passed. Entire-case durations were
respectively 2.073, 2.353, 2.528 and 2.167 seconds; these are not isolated maintenance
latency measurements. Exact property/timing evidence is retained in the summary.

This supports only the tested 100-parent/500-message workload and the runbook's
conditional bound: accurate clocks, available PostgreSQL/runner, ticks no more than
16 minutes apart, eligible workload clearing within five minutes and no sustained
capacity excess. It is not a guarantee for unbounded message cascades, unavailable
hosts, larger backlogs or unmeasured hardware. A failure of these assumptions needs
the owner's policy/capacity decision, not silent deadline relaxation. Account deletion
completion remains blocked by the identified query defect and is not accepted.

The three user-unit templates passed `systemd-analyze --user verify` using temporary
copies with this checkout's actual paths. Calendar syntax was previously verified.
No host timer was installed/enabled, no real scheduled execution was claimed, and
local journal failure visibility does not establish a staffed response. Actual host
scheduler/operational recovery remains a final acceptance verification item.

Disposable databases/roles were all removed; zero remained before removal of the
owned tmpfs PostgreSQL container and private password file. No unrelated resources,
coursework, CI workflows or security acceptance records were changed. Human CRITICAL
review remains unconfirmed and the expiry remains 23 October 2026, 23:59 EAT.
Fresh final-image evidence is recorded separately once the permitted rebuild/scan
finishes; image construction/scanning does not execute the corrected application.

### Final corrected image rebuild and scan evidence

The final backend runtime image was rebuilt from the new column-projection source;
all three immutable images were freshly scanned. See
[final manifest](security/p2-05/final-image-manifest.json) and
[final scan summary](security/p2-05/final-scan-summary.json).
Backend 44 HIGH/0 CRITICAL, PostgreSQL 71 HIGH/3 CRITICAL and web 0/0 remain:
115 HIGH/3 CRITICAL total, zero reported fixes or retrieved KEV matches. All complete
inventories match exactly (backend 119 packages, PostgreSQL 144, web 21); zero added,
removed or changed HIGH/CRITICAL occurrences. No package manifest/lock/pin changed.
The fresh scan of corrected packaged source is not execution or functional validation
of the remaining corrected account-deletion path, nor proof of vulnerability-free code.

The unchanged policy still rejects the new application exposure and its inherited
118 occurrences without an approved current decision: 119 reported failures, consisting
of the invalid exposure-bound risk decision plus each individually unaccepted finding.
The repository policy independently reports owner review required. All scan reports
exist and inventories validate; missing evidence is not being treated as a clean scan.
No acceptance, inventory/baseline or snapshot was changed to turn these gates green.

Next decision: authorize isolated synthetic execution of this exact new exposure for
three account-completion cases plus the strengthened physical-deletion audit rollback.
Do not repeat unaffected passing suites. Only after those pass can the separate minimum
five-file security-record proposal be finalized: active acceptance, byte-for-byte P2-04
snapshot at docs/security/p2-05/p2-04-acceptance-snapshot.json, this exposure assessment,
docs/SECURITY.md and AGENTS.md. No baseline/inventory-policy update is needed if the
fresh exact inventories/findings remain unchanged. Do not create that snapshot or alter
those acceptance records before explicit approval. Keep expiry/invalidation, daily
human reviews, all seven checks, scanning, branch protection and production prohibition.

## Final four-test authorization and consolidated record proposal

The owner authorized isolated testing of `bd6dd2b84da130225d8ffe115598329bc099721c`
with exposure `e363174d230cc0732e221d1bae835b0bc95bb6cc0921ef029c34b7a589ea797d`.
The three account-completion cases and strengthened physical-deletion audit rollback
all passed: **4/4 in 7.32 seconds**, no skips. No source correction was needed.
[Final validation evidence](security/p2-05/final-validation-summary.json) maps all
**28 privacy cases** to actual reports: 24 unaffected results retained plus four
fresh reruns, not a claim that one new 28-case run happened. Account cascade/retry,
held partial deletion/release, queue fairness and the intended injected audit fault
are now verified. Existing 14/14 targeted regressions, 22 contract, 49 unit and
11 frontend results are reused with their stated boundaries.

Migration 0006 pristine upgrade/downgrade and active-hold downgrade protection are
covered by the retained migration cases. The measured purge/catch-up/concurrency
and systemd-template evidence above remains valid. No unconditional deadline or
actual unattended host installation is claimed. All disposable test resources were
removed, with zero temporary test databases/roles left before container removal.

The final fresh image scan above has exactly this tested exposure. No code, package,
lockfile, network or privilege change followed that scan. Inventories and all 118
inherited occurrences are unchanged, with zero scanner-reported fixes/KEV matches.
The current strict CI risk gate still rejects the P2-05 exposure; functional success
is not an exception acceptance. No owner risk decision or human review is fabricated.

### One consolidated security-record approval requested

Approve a separate, narrowly scoped P2-05 synthetic-local-development acceptance for
tested source `bd6dd2b84da130225d8ffe115598329bc099721c` and the exact exposure above,
binding the existing baseline SHA-256
`0f48571f3b819b906b4aa78ce06c0beb4afd517283f78aad4e35c186d6056acf` and its individually
enumerated 118 occurrences: backend 44 HIGH; PostgreSQL 71 HIGH/3 CRITICAL; web 0/0.
The operator/deletion/security delta is the one reviewed above; no grants or network
exposure were broadened during corrections. This is not a production approval.

Only these five acceptance/documentation files would change after explicit approval:

1. `.github/security-risk-acceptances.json`: replace the active P2-04 decision with the
   explicitly approved P2-05 exact-exposure decision. Use the actual owner approval
   reference/time; preserve expiry, production=false and every invalidation condition.
2. `docs/security/p2-05/p2-04-acceptance-snapshot.json`: preserve existing active P2-04
   bytes exactly; expected SHA-256
   `70a67aaac3b95c86782534965cc1078fc7b24d7e6f45f6a28e6fcb24da90bc6e`.
   The file has not been created or approved yet; final-validation-summary independently
   records the actual source-byte digest for verification before any write.
3. `docs/P2_05_EXPOSURE_ASSESSMENT.md`: record the actual, separately granted decision.
4. `docs/SECURITY.md`: link the P2-05 exception, controls, evidence and limitations.
5. `AGENTS.md`: record the actual exact owner decision and permitted next workflow.

No baseline or inventory-policy update is necessary or proposed. Expiry stays
**23 October 2026, 23:59 EAT**; no renewal, suppression, broader finding acceptance,
production/real county or citizen data, automatic merge or future-exposure acceptance.
Daily actual human CRITICAL review remains mandatory and **unconfirmed**. That review
is separate from accepting the engineering exception and is not completed by tests.
All seven checks, complete scans, strict exposure binding and branch protection remain.

After explicit record approval only: apply those exact updates, verify byte integrity
and consistency, commit/push the feature branch, open the issue #21 PR and run normal
hosted checks. No merge is authorized. Keep P2-06 in a separate later branch/PR.

### Smallest optional iterative-runtime-testing amendment (proposal only)

Current AGENTS instructions require fresh explicit authorization whenever exposure
changes. The CI policy independently binds exception acceptance to an exact exposure;
neither currently grants automatic iterative execution. Ordinary backend test-only
changes outside that hash can proceed under the approved runtime scope, as already
demonstrated. No exception or policy amendment has been implemented here.

If the owner approves, add only this testing-only clause to AGENTS within the five-file
update: until the existing expiry, permit isolated synthetic test-driven corrections
limited to P2-05 defects and directly affected tests, **without expanding dependencies,
database privileges, listeners/network exposure, data classes or feature scope**.
Before execution, commit each correction, record its exact new commit/exposure and
security delta, rerun relevant static checks and obtain fresh complete dependency/
image-vulnerability evidence. Any new finding, fix availability, severity escalation,
KEV match, material exposure/privilege/network change or expired/revoked approval
requires a new owner decision before runtime. No automatic acceptance-record update,
CI bypass, merge, production use or human-review substitution is permitted. Final CI
exception acceptance remains separately exact-hash and owner-approved. This clause
reduces testing interruptions, not the final risk-acceptance requirements.
