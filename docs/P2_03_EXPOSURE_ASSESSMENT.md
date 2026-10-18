# P2-03 exposure assessment and runtime authorization checkpoint

Current status: the approved Docker remediation and controlled Compose validation
are complete; read the final section for the new exact exposure and remaining
security-record checkpoint. Earlier sections retain the pre-remediation evidence.

Date: 18 October 2026. Updated after the explicitly authorized limited backend/PG
validation below. This is an assessment and actual test report, not a development
risk acceptance, web/Compose runtime permission or production approval. Issue #19's persistence
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
These controls were source-reviewed at the initial checkpoint. The limited backend/PG
validation below now verifies the covered cases; it is not a claim of complete security.

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

The owner explicitly authorized commit 0dd84f9658c1c8dae4beee9a1fac4214658b4088
with unchanged exposure f0fa257c41dc225ba807ffd87aba15897fc1f77bde82323d56ed6782b6fe32b3
for isolated backend/PostgreSQL tests. Actual results: **25/25 unit/contract cases
passed in 0.11 seconds; 20/20 PostgreSQL integration cases passed in 35.42 seconds**,
zero failures/skips. Each suite emitted the existing Starlette TestClient/httpx
deprecation warning. No application or test corrections were required.

Sanitized, validator-accepted JUnit evidence: [unit results](security/p2-03/unit-results.xml)
and [PostgreSQL results](security/p2-03/postgresql-results.xml). The earlier scan-summary
prepared_tests entries are the historical initial checkpoint, not current execution
status. Updated existing metadata/revision/OpenAPI and Compose schema assertions
remain prepared for their relevant full-suite replay after approval. Tests cover ownership/401/404, role injection, content/byte caps,
idempotency conflict/replay, concurrent same/different-key writes and metadata PATCH,
sequence/pagination under writes, retention/language snapshots, storage caps,
FK/CHECKs, cascade deletion, least-privilege grants, mandatory-audit failure rollback,
and destructive disposable downgrade/re-upgrade preserving identity.

For the subsequently authorized full regression run, use the existing locked Python 3.12 backend
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

## Historical web remediation proposal (subsequently authorized below)

Installed libexpat remains 2.8.5-r0 in the existing full Alpine web image; vendor fix
is 2.9.0-r0. Docker Hub inspection confirms stable-alpine still resolves to the
existing 782bb897... digest, so repulling the same tag does not remediate it.

A vendor-published alternative is nginxinc/nginx-unprivileged:stable-alpine-slim
at sha256:4ac59c85c8c46d9e91eaabd2122cda4923ba380cf11f4138e389f069bcdc77a3.
It removes unused dynamic-module dependencies, including libexpat, rather than
claiming to contain the patched package. The [vendor slim Dockerfile](https://github.com/nginx/docker-nginx-unprivileged/blob/main/stable/alpine-slim/Dockerfile)
installs core Nginx; the [full variant](https://github.com/nginx/docker-nginx-unprivileged/blob/main/stable/alpine/Dockerfile)
adds XSLT/GeoIP/image-filter/NJS modules. Our configuration loads none of these.

This candidate base was pulled, inspected/exported without starting a container,
and scanned by immutable ID with the same complete-inventory scanner controls.
Result: 21 packages, no libexpat, zero HIGH/CRITICAL findings. Same Nginx 1.30.6 and
UID 101; /bin/sh, sed, awk, mime.types and nginx binary present by static inspection.
No explicit proxy-module disable flag was found in the binary. This is static
compatibility evidence, not a successful nginx -t, web startup or end-to-end test.
The candidate is not asserted free of all vulnerabilities.

Only frontend/Dockerfile needs a technical image-selection change. The exact
[proposed one-line patch](security/p2-03/web-base-remediation.patch) passes
`git apply --check` and is **not applied**. [Candidate scan evidence](security/p2-03/web-remediation-scan-summary.json)
records the immutable ID, report checksum and full package identity/version list.
Full candidate report: /tmp/county-p203-web-slim-scan.json. No affected web image or
Compose runtime was executed. No package override or vulnerability suppression was
introduced. The candidate changes web inventory from 70 to 21 packages, so it cannot
inherit the old package inventory approval even with zero HIGH/CRITICAL findings.

## Execution environment and cleanup

Only the two authorized suites were executed, on the approved source/hash.
PostgreSQL 17 used a unique disposable container, random database/role names,
private generated password file, custom bridge network, ephemeral loopback-only
host port, non-root UID 999, read-only root, tmpfs data, dropped capabilities,
no-new-privileges and bounded resources. Fixture-created DBs/roles and harness-owned
container/network/password directory were removed. Unrelated developer containers
were untouched. A first harness attempt could not obtain a published port on an
internal network and failed before pytest; the harness was corrected to a separate
bridge with loopback publication. No project source/exposure change was needed.
No web container was started. Static checks passed again after validation.

## Historical checkpoint before web remediation authorization

Limited backend/PG validation is complete. The code exposure remains exactly the
approved f0fa257c... hash; no automatic future-source approval is assumed.

Next approval is needed to apply the proposed single-line frontend/Dockerfile
variant/digest patch, build/scan the assembled web artifact and validate web/Compose
compatibility against its newly reported exact source/exposure. Existing security
acceptance/inventory/baseline records must remain unchanged until a separate owner
policy decision covers the exact assembled images, inventory and residual findings.
The technical patch does not itself grant permission to update those records.

Full CI/PR readiness is still blocked by unapproved P2-03 exposure and current web
fixable finding. After reviewed remediation, the policy procedure will need explicit
approval for .github/security-baseline.json, .github/security-inventory.json and
.github/security-risk-acceptances.json, plus preservation of the previous acceptance
as a historical snapshot and associated assessment documentation. No such changes
are made or pre-approved here; exact record updates require the completed evidence.

Today's actual human CRITICAL review is still unconfirmed and has not been marked
complete. All seven CI checks, scanning, branch protection and invalidation rules
remain active. Expiry remains 23 October 2026, 23:59 EAT. No push, PR, merge,
real citizen/county data, production credentials, public deployment or Phase 3 work.

## Completed Docker remediation and consolidated security checkpoint

The owner authorized the prepared base replacement and isolated synthetic web/Compose
validation on 18 October. Runtime/test source commits: ff89b997fceb74ac2d95d0868d7ff69a3ec9ac69
(one Dockerfile line), 84ff611 (unit-test filename correction) and
8fe5d2ec3b6d6ec334ce95bdb65782b24d89813d (bounded suite harness timeout), followed
by 6b3a201 (auth smoke schema expectation correction).
Subsequent documentation/evidence commits do not change the application exposure.

Final exposure: **88669fbe4cfafc7dc45e6775546e44e6ca8bcbec1dcacfb0f89a36c702af19b4**.
No backend application, authentication, Nginx configuration, dependency lock or
security policy algorithm changed during remediation. No previous acceptance was
inherited. No acceptance/baseline/inventory-policy records have been edited.

### Change and actual runtime results

frontend/Dockerfile now uses vendor stable-alpine-slim at the owner-approved digest
4ac59c85c8c46d9e91eaabd2122cda4923ba380cf11f4138e389f069bcdc77a3.
It removes unused modules/dependencies, rather than installing an ad hoc APK override.
The application still uses Nginx 1.30.6, UID/GID 101, identical configuration and the
same startup script. Only the remediated web image was used for runtime tests.

The assembled/scanned web image is
sha256:8d52ce476c83a44926cbb9a40222dfa88440b502f7fba22753e401415565f951.
The [actual Compose manifest](security/p2-03/remediated-runtime-manifest.json) was
compared against all three fresh scans of the actual Compose build before startup:
exact immutable IDs match. Earlier standalone-build scans were not substituted
for different Compose output IDs.

The controlled Compose/browser flow completed successfully using the already-passing
51-case PostgreSQL result with verified unchanged backend/test bytes. All remaining
normal exercise stages were executed. The hosted workflow still invokes the full
unmodified mandatory test commands; no CI skip/reuse option was added. Results:

- Non-root processes, read-only roots, capability drops, secret/network/loopback
  isolation and denied runtime DDL/revision writes.
- Actual frontend serving, SPA refresh, missing-asset behavior and API error proxying;
  fresh live=200/ready=503, explicit repeatable migrations and ready=200.
- **51 real-PostgreSQL regression cases passed**, including the 20 persistence cases
  replayed by the mandatory normal runner. The earlier 25 unit cases were not rerun.
- **Two actual-Nginx Chromium tests passed**: foundation navigation/language/refresh
  and authentication/activation/logout/own-session flows. All nine auth routes,
  cookie/CSRF rejection, refresh reuse and revocation checks passed through Nginx.
- Database outage/recovery, graceful backend replacement and proxy DNS recovery,
  independent UI serving, named-volume persistence, persisted account/session checks
  after down/up, clean shutdown and secret canaries absent from logs/inspect/history.
- Owned disposable containers/networks/volumes and temporary configuration cleaned
  up; no existing development project targeted.

Sanitized evidence: [Compose passes/reuse](security/p2-03/remediated-compose-results.txt),
[previous normal PostgreSQL pass](security/p2-03/remediated-postgresql-pass.txt),
[foundation browser](security/p2-03/remediated-compose-browser.xml),
[authentication browser](security/p2-03/remediated-auth-browser.xml) and
[tooling safety tests](security/p2-03/remediation-tooling.xml). The legacy console
label 'identity-only schema' corresponds to an assertion including both identity
and conversation tables; it is not an assertion that conversation tables are absent.

### Narrow test/evidence corrections

The first normal replay exposed a collection collision between unit and integration
files both named test_conversations.py. The unit file was renamed unchanged to
backend/tests/test_conversation_contracts.py. Combined discovery then collected all
157 cases. No tests were removed, skipped, weakened or given fabricated results.
The 31 existing PostgreSQL cases also passed in isolated diagnostic execution.

The expanded containerized suite then exceeded the old 180-second subprocess limit.
Only that test-harness limit in scripts/compose_smoke.py was raised to a bounded
600 seconds. Application/database timeouts, scan timeouts, CI job limits, thresholds
and required commands were not changed. The mandatory full PostgreSQL replay then passed (51 cases). Its following auth
smoke assertion exposed a pre-P2-03 exact OpenAPI path set; only the three approved
conversation paths were added in scripts/auth_compose_smoke.py, retaining every auth
path assertion. This independent test correction does not change backend/test bytes.
To avoid another unnecessary 51-case replay, the remaining local flow reused that
validated PG result; the reuse driver checked git diff against the successful source,
unchanged exposure and the preserved successful backend test image. This local driver is outside the
repository; hosted CI has no skip, reuse hook or weakened command.
These test-only corrections leave the application exposure hash unchanged. Ruff,
formatting, strict Mypy and repository/documentation validation passed; the four
relevant cleanup/vulnerability-gating tooling tests passed. No unrelated suite was
rerun. Known TestClient deprecation/terminal-color warnings are not failures.

### Fresh security delta

[Fresh complete scan summary](security/p2-03/remediated-scan-summary.json) retains
checksums, immutable IDs, every HIGH/CRITICAL row, inventory hashes and KEV results.
Full reports remain in /tmp/county-p203-actual-runtime-scans. Trivy was 0.76.0 with
all-package reporting and no ignore/config overrides. Source/build dependencies and
backend/PostgreSQL package inventories are unchanged.

| Image | HIGH | CRITICAL | Inventory packages | Fixable HIGH/CRITICAL |
| --- | --- | --- | --- | --- |
| Remediated web | 0 | 0 | 21 (previously 70) | 0 |
| Backend | 44 | 0 | 119 (unchanged) | 0 |
| PostgreSQL | 71 | 3 | 144 (unchanged) | 0 |

Exactly **115 HIGH + 3 CRITICAL = 118 inherited occurrences** remain. None changed
by class/CVE/package/version, severity, fix or vendor-status fields; no new findings
or retrieved-KEV matches were found. The web has 49 removed packages, zero added or
version-changed retained packages. libexpat 2.8.5-r0 and CVE-2026-77214 are absent.
The new web inventory SHA-256 is
e9d19af8839b51cd311f6b527994b6cc624ee2b0491513c293f6fefa6cb60443.
This is removal of the vulnerable dependency, not a claim that libexpat 2.9.0 is
installed or that the whole application is vulnerability-free.

The SQLite CVE-2025-7458, libxml2 CVE-2026-6653 and zlib CVE-2023-45853 assessments
above remain applicable for human review. No actual daily human review is asserted.
Production remains prohibited; no real citizen data or production credentials were
used. Runtime success is not a new development risk acceptance.

### One proposed owner decision: exact seven-file security-record update

Approve only the following subsequent updates for the exact reviewed source/exposure
and unchanged 118 inherited OS-package/CVE occurrences, synthetic isolated local
use only, expiry unchanged at **23 October 2026, 23:59 EAT**:

1. .github/security-baseline.json: replace only web base_digest/image_id/report_sha256
   with the reviewed slim digest, assembled image and fresh report checksum; keep
   its findings empty and all backend/PostgreSQL entries byte-equivalent. Set
   snapshot_date to 2026-10-18 and source to the exact text below. No finding removal
   or suppression from the inherited accepted rows.
2. .github/security-inventory.json: replace only web inventory (21 packages and hash
   above) and web source_report_sha256 to match the new baseline's web report.
   Backend and PostgreSQL inventory entries remain unchanged.
3. .github/security-risk-acceptances.json: create a separate, explicitly owner-approved
   P2-03 decision bound to the exact new exposure and baseline hash. Keep
   production_allowed=false, the existing expiry, all invalidation triggers and
   actual daily human CRITICAL review requirement; no automatic future approvals.
4. docs/security/p2-03/p2-02-policy-snapshot.json: preserve the pre-update baseline,
   complete inventory and P2-02 acceptance as original UTF-8 bytes plus SHA-256,
   without altering earlier Phase 1/P2-01 snapshots or reattributing approvals.
5. docs/P2_03_EXPOSURE_ASSESSMENT.md: record the actual owner decision and limits.
6. docs/SECURITY.md: document the separately approved P2-03 restricted-development
   scope and remediation; retain production prohibition and expiry.
7. AGENTS.md: record the same exact approved scope and stop boundaries.

Exact proposed baseline source text:

```text
P2-03 web-only remediation evidence; backend and PostgreSQL baseline records retained unchanged from the prior reviewed snapshot
```

With these exact fields serialized as existing sorted, two-space-indented JSON plus
final LF, the proposed baseline SHA-256 is
0f48571f3b819b906b4aa78ce06c0beb4afd517283f78aad4e35c186d6056acf.
The current baseline hash remains
3b4b2b44866f00c4d24d219b6ee0e4e7428bbc81362af9bc8313e39615c5d234.
The new web report SHA-256 is
b01ee40624627654afb3b6d405ad706a41a13317a48a5e19f959220ff1231071.

The owner must also perform today's actual human review of the three CRITICAL
assessments; no automated check or this document substitutes for that review.
Only after the explicit decision may these seven files be updated and normal
policy checks rerun. No acceptance, expiry, baseline or inventory-policy update
has been applied now. Push/PR/merge remain unauthorized at this checkpoint.

### Current CI readiness

Functional Compose checks passed. Security policy correctly still fails: changed
exposure requires owner review, and the web inventory/base no longer matches the
old approved policy. The scanner's generic 'web scan evidence missing, invalid or
unavailable' is raised by validate_inventory for the 70 -> 21 package change, not
a missing report or clean-scan assumption; complete scanner evidence validates
independently. All seven hosted contexts remain required and have not been run on
this branch. No workflow/ruleset/scan override changed. PR submission still waits
for the explicit record decision, actual human review and remaining owner workflow
authorization. No push, PR, merge or production deployment occurred.

## Owner-approved P2-03 records, 18 October 2026

The owner explicitly approved the seven-file update for f9520eb932341a150f26ea1d977b8fff67a51c7d,
exposure 88669fbe4cfafc7dc45e6775546e44e6ca8bcbec1dcacfb0f89a36c702af19b4,
web inventory 21 packages and unchanged 115 HIGH/3 CRITICAL inherited occurrences.
Previous P2-02 policy bytes are preserved in docs/security/p2-03/p2-02-policy-snapshot.json.
Expiry remains 23 October 2026, 23:59 EAT. Synthetic isolated local development only;
no real data or production deployment. All invalidation triggers, seven checks, scans,
branch protection and owner PR review remain mandatory. Push and PR linked to issue
19 are now authorized; no merge. Human CRITICAL review for today remains pending: no
review completion is asserted. Automated policy does not require a human-review
timestamp before CI; documented human acceptance obligations remain incomplete even
if CI passes. This approval does not grant unconditional milestone acceptance.
