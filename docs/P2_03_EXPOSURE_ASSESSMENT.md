# P2-03 exposure assessment and runtime authorization checkpoint

Date: 18 October 2026. This is an assessment, not a security acceptance, runtime
permission, passing-test report or production approval. Issue #19's persistence
amendment was explicitly approved by the owner before implementation.

## Exact source and scope

Branch: feat/p2-03-conversation-persistence. Source/test commit:
af7dd68fc5399b7b536efc99d7a7fc8473409d93. Subsequent assessment-only documentation
commits do not alter the exposure hash; the final head must be reported separately.
Parent main: 5ff0e2281ed7f4984ffcb090a3c87c14157fd800 (merged PR #25).

- Previous accepted P2-02 exposure:
  0b8f2dc7e55e72fbc96325edbec4d57a5a97c9eb52d4fae3251e9aec302b958d.
- Prepared P2-03 exposure:
  f0fa257c41dc225ba807ffd87aba15897fc1f77bde82323d56ed6782b6fe32b3.

No runtime dependency, lockfile, container base, frontend source, workflow, branch
rule or security acceptance/inventory/baseline record changes. Backend and tooling
exact-lock audits both report zero advisories. This does not prove the application
or its dependencies vulnerability-free.

## New surface and controls

Seven handlers on three conversation paths are added behind the existing explicit
auth-enabled switch: collection POST/GET, item GET/PATCH/DELETE, messages POST/GET.
No authentication API is changed. Live session/account bearer validation remains
mandatory; cookies alone cannot authorize persistence. Unknown, expired and other-
owner resources return concealed 404s; admins do not bypass ownership.

Authenticated users gain text storage, bounded history and deletion. New risks are
IDOR/mass assignment, storage and lock contention, duplicate/reordered writes,
optimistic-update races, retention violations and accidental content logging.
Prepared controls include scoped predicates on every operation, account -> family
-> conversation locks, key/sequence uniqueness, strict content-only message bodies,
32 KiB streaming body cap, 4,000-character content limit, user-only database CHECK,
100 live conversations/account, 1,000 messages/conversation, bounded signed cursors,
ETags, immediate logical expiry and atomic cascading deletion. Existing global
admission/rate controls and query/lock timeouts remain; no throughput claim is made.

Runtime grants add only conversation SELECT/INSERT/DELETE and named metadata/counter
UPDATE columns; messages permit only SELECT/INSERT. Audit records are content-free
pseudonymous mutation events and must commit with changes; audit/DB failures must
roll back and return safe 503. The shared body limiter now also bounds conversation
paths. No logs include content, tokens, cursor values, raw errors or credentials.
These are source-reviewed controls, not runtime-verified claims at this checkpoint.

The new SQL text is parameterized; no arbitrary SQL, XML input, archive processing,
provider dispatch, tool execution, new listener or real data is introduced. The
three inherited CRITICAL findings are reassessed below, without claiming a proof
of non-exploitability. Physical purge remains P2-05, not a completed P2-03 feature.

## Fresh immutable-image evidence

The new backend runtime image was built without starting its service. Unchanged
web/database runtime images were rescanned by immutable ID with Trivy 0.76.0,
all-package inventory and no ignore/config overrides. Scan time was approximately
16:46 UTC on 18 October. Vulnerability DB UpdatedAt was 2026-10-18T13:11:41Z.

| Image | Immutable image ID | HIGH | CRITICAL | Fixable HIGH/CRITICAL |
| --- | --- | --- | --- | --- |
| web | sha256:e83a7ef367f49e6e716e96797c55c59c29e66269ef7681efc068fb4de6a61469 | 1 | 0 | 1 |
| backend | sha256:72a762a0103eb2e5e061963b018a302e2036b53bdf8c87fbefb4ca41a56aec87 | 44 | 0 | 0 |
| PostgreSQL | sha256:f52049cb7e9fae14fc73d6ed63842489e6aeda9ee855450aecd842167e9731d7 | 71 | 3 | 0 |

Total: **116 HIGH and 3 CRITICAL**, 119 package/CVE occurrences. The 118 inherited
occurrences are unchanged by exact class/CVE/package/version, severity, status and
fix fields; none were removed. A new finding in unchanged web is separate from
the P2-03 source delta:

- CVE-2026-77214, libexpat 2.8.5-r0, scanner HIGH; fixed version 2.9.0-r0.
  The [Alpine security tracker](https://security.alpinelinux.org/vuln/CVE-2026-77214)
  independently identifies the XML_ParseBuffer heap over-read and fixed package.
  This confirms an advisory/fix, not exploitability in our Nginx configuration.
  No exploit was executed or reachable application path demonstrated. Presence
  cannot be dismissed as local-only; the newly discovered/fixable finding invalidates
  the relevant prior exception and blocks Compose/security-policy readiness.
  It is not proposed for acceptance; a reviewed image remediation is needed.

All HIGH/CRITICAL findings are OS packages; no language-package HIGH/CRITICAL finding
was reported. None matches the fresh retrieved CISA KEV snapshot recorded in the
[evidence summary](security/p2-03/scan-summary.json). Absence from KEV is not proof
of no exploitation. Full scanner reports/KEV/decision remain at
/tmp/county-p203-scans on this environment; SHA-256 checksums, immutable IDs,
complete inventory hashes and every HIGH/CRITICAL row are retained in the summary.
The summary is a derivative assessment, not a replacement scan report or policy file.

## Complete dependency inventories

All three inventories match the existing policy byte-for-byte by stable package
identity/version inventory hash; there are **zero additions or removals**:

| Role | Packages | Inventory SHA-256 |
| --- | --- | --- |
| web | 70 | 7e79131d8a8bfb174b281e86f0f1ecc5495a7df6c29242b0605affe1f2de6682 |
| backend | 119 | 7c9d236e62e9b96b9dfe7ca03dd92b1d999c6bacfb7fb8f67949a9790d88274e |
| db | 144 | f0ff6951e8f3157a9f0e6d15387c68b6e4e591afd21d2d0da972c122ed1ad288 |

Changed source bytes still invalidate prior exposure approval even though dependency
inventories are unchanged. Newly published findings can also invalidate an exception
without any package change, as the web scan now demonstrates.

## Three inherited PostgreSQL CRITICAL assessments

| CVE / package | Current fix status | P2-03 exposure assessment |
| --- | --- | --- |
| CVE-2025-7458 / libsqlite3-0 3.40.1-2+deb12u2 | No scanner fix; affected | Crafted SQLite SQL prerequisite in prior assessment; persistence uses PostgreSQL parameterized queries, not SQLite. No new direct API path identified; no exploit reproduced. |
| CVE-2026-6653 / libxml2 2.9.14+dfsg-1.3~deb12u6 | No scanner fix; fix_deferred | PostgreSQL SQL/XML remains a plausible path after SQL/credential compromise. No XML parsing or arbitrary-SQL endpoint is added. New DB operations require renewed owner exposure review; no exploitability conclusion from scanner presence alone. |
| CVE-2023-45853 / zlib1g 1:1.2.13.dfsg-1 | No scanner fix; will_not_fix | Prior Debian assessment says vulnerable MiniZip code excluded from these binaries; retain the scanner occurrence. No archive/ZIP API added; no reproduced exploit. |

The prior register's detailed references/compensating controls still apply as
assessment context, not automatic approval for new source. No actual human CRITICAL
review for 18 October is asserted by this report. An actual dated owner review
remains required. Non-root/read-only/capability/network isolation and synthetic-only
operation are preserved, but have not been replayed against changed runtime yet.

## Actual checks and pending execution

Passed: Ruff lint/format for backend and changed smoke script; strict Mypy (33 source
files); repository document/config check; git diff whitespace check; Gitleaks current
files (no leaks); exact backend and tooling dependency audits (zero advisories).
The runtime image build completed. Mermaid source is documented; visual rendering
has not been verified. No host dependency installation or coursework execution occurred; the image build
installed only the unchanged locked dependency set.

Prepared, **not executed**: 25 new parameterized unit/contract cases and 20 real-PG
integration cases, plus updated existing metadata/revision/OpenAPI and Compose
schema assertions. Tests cover ownership/401/404, role injection, content/byte caps,
idempotency conflict/replay, concurrent same/different-key writes and metadata PATCH,
sequence/pagination under writes, retention/language snapshots, storage caps,
FK/CHECKs, cascade deletion, least-privilege grants, mandatory-audit failure rollback,
and destructive disposable downgrade/re-upgrade preserving identity.

After explicit runtime authorization, use the existing locked Python 3.12 backend
from backend/: `.venv/bin/python -m pytest -q -m 'not integration'` and the real-PG
suite `.venv/bin/python -m pytest -q -m integration` with the documented loopback
COUNTY_TEST_ADMIN_URL and COUNTY_TEST_DISPOSABLE=YES. Keep credentials in private
configuration, never commands/logs. Generate actual JUnit reports. Compose checks
require separate resolution of the new fixable web finding before readiness claims.

The unchanged policy checker currently rejects the new exposure. The full image
scanner also correctly rejects the new fixable web occurrence and the absent new
risk decision. These failures are expected enforcement, not clean scans, missing
inventories or passing CI. All seven mandatory contexts remain unchanged; no hosted
changed-runtime CI was dispatched and no PR/push/merge occurred at this checkpoint.

## Required human decision

Request isolated, synthetic-only **backend and PostgreSQL** unit/integration runtime
validation of the exact source commit and exposure above, with no web/Compose
runtime or production use, no acceptance/hash/inventory-file changes, no expiry
extension, and all scans/checks/rules retained. Separately resolve the fixable web
image finding before full Compose/hosted security readiness. Validation permission
would not make CI green or create a new development risk acceptance.

The owner must also perform today's actual review of the three CRITICAL assessments.
Any later source correction requires reporting its new exact exposure/security delta;
no automatic approval of future changes is assumed. Existing expiry remains
23 October 2026, 23:59 EAT. No real citizen/county data, production credentials,
public deployment, automatic renewal, PR merge, frontend history or Phase 3 work.
