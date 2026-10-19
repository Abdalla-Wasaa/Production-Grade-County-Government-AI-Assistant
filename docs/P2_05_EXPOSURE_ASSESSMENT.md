# P2-05 source checkpoint and focused exposure assessment

Status: source prepared on 19 October 2026, **runtime authorization pending**.
Implementation and prepared-test commit: `969535e` (documentation-only follow-up
commits do not change the exposure). Branch: `feat/p2-05-privacy-lifecycle`.
Base: merged P2-04 PR #27, `a7902700e10dcd6fc71ebf582ba84fada1d93254`.
This document records evidence and requests testing permission. It is not a security
acceptance, a human CRITICAL review or a passing application-test report.

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
