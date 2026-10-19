# P3-01 focused exposure assessment — runtime approval pending

## Scope and prerequisites

The latest owner authorization and updated issue #30 explicitly defer Ollama to
P3-02. Current source is fake-only; the superseded, unpushed Ollama preparation was
removed and its HTTP runtime dependency promotion reversed. Final dependency files
are byte-identical to main. No model install, live inference or application test has
executed for this source. Packaging-only image builds/scans and static checks ran.

PR #29 is owner-merged at `379a43957e65b3acb2c5e19b5fdea90d70f878f7`, with all seven
mandatory checks passing. Issue #22 records Phase 2 COMPLETE for restricted synthetic
development only. Branch: `feat/p3-01-provider-abstraction`.

Source commit: `62e8e3ae78b53085b779ae350599c6c3a1d8e63f`.
Documentation/evidence commits after this source do not change its exposure.

| Binding | SHA-256 |
| --- | --- |
| Previous approved application exposure | e363174d230cc0732e221d1bae835b0bc95bb6cc0921ef029c34b7a589ea797d |
| P3-01 application exposure | 54a7c2e7d075593f17107dd652edf035b28b7a399611f700c095bc5f1b04ecc4 |
| Backend inventory, 119 packages | 7c9d236e62e9b96b9dfe7ca03dd92b1d999c6bacfb7fb8f67949a9790d88274e |
| PostgreSQL inventory, 144 packages | f0ff6951e8f3157a9f0e6d15387c68b6e4e591afd21d2d0da972c122ed1ad288 |
| Web inventory, 21 packages | e9d19af8839b51cd311f6b527994b6cc624ee2b0491513c293f6fefa6cb60443 |

## Source and security delta

Added typed asynchronous provider/model identity/request/result/usage/error contracts,
validated fake/fake-v1 selection, explicit implemented-provider registry, managed
deadline/admission/concurrency wrapper and deterministic bilingual fake. Existing
FastAPI lifespan constructs/closes the provider without calling generation.

No route, listening port, outbound transport, credential requirement, database schema,
role/grant, conversation/authentication/privacy behavior or CI workflow was added.
Health/readiness remains independent of inference. Tests clear provider environment
variables, select fake and retain existing external-socket denial.

New code still creates risk: lifecycle cleanup, cancellation/admission handling,
validation and exception normalization can contain defects. Tests are prepared to
challenge these; static checks and unchanged scanners do not establish bug-free or
vulnerability-free code. The fake has explicit test-constructor delay/failure controls,
not a user-facing fault API. Private message content is hidden from representations,
not emitted by the fake and not explicitly logged by provider code.

The existing SQLite CVE-2025-7458, libxml2 CVE-2026-6653 and zlib CVE-2023-45853
CRITICAL assessments remain as individually recorded in the vulnerability register.
This fake-only boundary introduces no SQL/XML, SQLite, compression or network input
path to those packages. No new reachability path was identified in this focused
review; no exploit-reproduction claim is made. Daily actual human review remains
mandatory. The owner's 19 October review applies to that date only.

## Complete packaging and dependency evidence

[Fresh scan summary](security/p3-01/scan-summary.json) and
[immutable image manifest](security/p3-01/image-manifest.json) bind all three image
reports, Trivy database freshness, inventories and full HIGH/CRITICAL occurrence
comparison. Raw reports are generated locally with unchanged `scan_images.py`.
They remain outside source control; summary report hashes preserve provenance.

| Runtime | HIGH | CRITICAL | New/removed HIGH or CRITICAL occurrences | Reported fixes / KEV matches |
| --- | --- | --- | --- | --- |
| Backend | 44 | 0 | 0 / 0 | 0 / 0 |
| PostgreSQL | 71 | 3 | 0 / 0 | 0 / 0 |
| Web | 0 | 0 | 0 / 0 | 0 / 0 |

All complete inventories match main. No dependencies, versions or lock entries
changed. [Dependency audit](security/p3-01/dependency-audit-summary.json) covers the
same exact resolved package versions and reports zero backend/tooling advisories.
Existing remediated Nginx pin and its reviewed/deferred tag-drift disposition remain
unchanged; this milestone does not change the image pin or suppress its monitor.

The normal policy scan exits nonzero: the active acceptance cannot bind the changed
exposure. Inherited findings therefore lack applicable P3-01 acceptance in this run.
All three raw reports and inventory checks are valid; this is an owner-decision
failure, not missing backend scan evidence. Do not manufacture a passing decision,
edit inventories or reinterpret this as acceptance.

## Prepared validation and exact next decision

Static checks passed: Ruff lint/format, strict Mypy, dependency audit and secret scan.
Repository documentation/link validation follows this assessment addition. The normal
workflow-policy checker correctly rejects the new exposure. No application tests,
Pytest collection, application server or provider generation ran.

There are 43 prepared provider cases (static AST count, not runtime results):
determinism, English/Kiswahili, fixed failures, timeout, admission/concurrency,
cancellation, invalid settings/requests, metadata mismatch, sensitive-error/logging
protection, health/lifecycle closure and unsupported factory choices. Retain valid
Phase 2 PostgreSQL/browser/infrastructure evidence where unaffected; run the full
existing non-integration backend suite because composition and test fixtures changed.

**Requested decision:** authorize isolated synthetic-only execution of the exact
P3-01 exposure above, its 43 provider cases and existing non-integration backend
regressions, with no network/model/provider downloads. Any correction changing
exposure must follow the current exact-hash authorization procedure before execution.
This is testing-only: no risk-acceptance/baseline/inventory edits, push, PR, merge,
expiry extension or live inference. After actual results, request any separately
required security-record decision before publication/hosted CI.

Existing expiry remains **23 October 2026, 23:59 EAT**. No production deployment or
real citizen/county data. All seven required checks, complete scanning, historical
records, logging protections and branch protection remain unchanged. No automatic
inheritance of Phase 2 acceptance or iterative-testing policy exception.
