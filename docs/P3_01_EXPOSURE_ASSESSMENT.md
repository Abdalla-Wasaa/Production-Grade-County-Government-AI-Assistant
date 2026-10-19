# P3-01 focused exposure assessment — validation passed; owner acceptance applied

## Scope and prerequisites

The latest owner authorization and updated issue #30 explicitly defer Ollama to
P3-02. Current source is fake-only; the superseded, unpushed Ollama preparation was
removed and its HTTP runtime dependency promotion reversed. Final dependency files
are byte-identical to main. No model install or live inference has executed. After the owner authorized
b7827d8 / the exact exposure below, provider and backend tests ran with synthetic
inputs only; the dated results below supersede the initial testing checkpoint.

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

Before the separate owner approval below, the normal policy scan exited nonzero:
the Phase 2 acceptance could not bind the changed exposure. Inherited findings therefore lacked applicable P3-01 acceptance in that initial run.
All three raw reports and inventory checks are valid; this is an owner-decision
failure, not missing backend scan evidence. Do not manufacture a passing decision,
edit inventories or reinterpret this as acceptance.

## Authorized validation results and exact next decision

The owner explicitly authorized isolated synthetic testing of commit
`b7827d8ce4346d0f1ef8f987a2f7931945d869ff` and exposure
`54a7c2e7d075593f17107dd652edf035b28b7a399611f700c095bc5f1b04ecc4`.
Actual results on 19 October 2026:

| Execution | Passed | Failed / skipped | Duration |
| --- | --- | --- | --- |
| Provider contracts, fake determinism, bilingual inputs, invalid settings/requests, fixed failures, timeout, cancellation, concurrency, model identity, lifecycle and private logging | 43 | 0 / 0 | 0.36 seconds |
| Existing non-integration backend regressions, including auth/conversation/privacy contracts and logging | 128 | 0 / 0 | 3.02 seconds |

These were two invocations, not a newly claimed single combined suite. The existing
79 PostgreSQL cases were explicitly deselected; retain their passing merged-main
provenance for unchanged identity/conversation/privacy SQL and migrations. No schema,
grant, SQL, frontend or network-source change requires repeating those suites here.
No correction was needed, so tested source/exposure is unchanged. A pre-existing
Starlette TestClient/httpx deprecation warning is recorded; no dependency was added
or upgraded to silence it.

[Validation summary](security/p3-01/validation-results.json),
[sanitized provider report](security/p3-01/provider-results.xml) and
[sanitized regression report](security/p3-01/backend-regression-results.xml)
record actual evidence. The repository report validator accepted both reports;
none of their cases failed or skipped. Existing socket denial remained active for
all executed cases; the fake requires no network client or credentials. Tests verify
private prompt representations, safe exception text and no content in captured logs.
Ruff lint/format and strict Mypy also pass. No application source changed after tests.

Fresh immutable image scans from 19 October remain valid for this exact source and
unchanged inventories; no rebuild is needed for evidence-only documentation changes.
Raw report hashes/KEV/scanner freshness are rechecked rather than rerunning unchanged
images unnecessarily. They show exactly the same 115 HIGH/3 CRITICAL occurrences,
no added/removed reviewed findings, no reported fixes and no retrieved KEV match.
Dependency audit reports no advisories and dependency files remain byte-identical
to merged main. This is not proof that the new code has no vulnerabilities.

### Owner-approved five-file decision

Testing authorization was separate from security acceptance. The owner subsequently
approved the narrowly scoped P3-01 decision binding this tested exposure and the
exact same 118 individually enumerated baseline occurrences, with all existing
invalidation rules and daily human CRITICAL review. Baseline/inventory records
remain unchanged; the active acceptance and historical snapshot now reflect only
the explicitly authorized five-file update.

Only these five files changed under the explicit approval:

1. `.github/security-risk-acceptances.json`: bind the separate P3-01 decision to this
   reviewed/tested exposure and unchanged baseline; no new findings or future exposure.
2. `docs/security/p3-01/p2-05-acceptance-snapshot.json`: preserve current Phase 2/P2-05
   acceptance JSON bytes exactly before updating the active decision. Current bytes
   have SHA-256 d7e62ed76852a7646cc6cdf5908bad210b33ea2cc989521007988b8aade46c3e.
3. `docs/P3_01_EXPOSURE_ASSESSMENT.md`: record the exact owner decision and its scope.
4. `docs/SECURITY.md`: document the current restricted-development decision.
5. `AGENTS.md`: record the exact authorized scope without altering permanent rules.

No baseline or inventory-policy update is needed or proposed. The decision must
preserve expiry 23 October 2026, 23:59 EAT, daily actual human CRITICAL reviews and
invalidation on fixes/new findings/escalation/KEV/exposure/dependency changes.
The owner explicitly authorized publication alongside that five-file decision:
commit/push this branch, open the PR linked to #30 and run all seven normal hosted
checks. No automatic merge or live inference. A draft PR description is prepared
outside tracked application files; no PR has been opened.

### P3-02 handover

The async protocol, typed provider/model identity, managed deadline/cancellation,
factory registry and mocked adapter tests provide the boundary for a later Ollama
HTTP adapter and configuration-driven model selection without changes to identity,
privacy, conversation business logic or frontend code. P3-01 deliberately rejects
Ollama selection today. P3-02 must add its own validated endpoint/model settings,
HTTP transport/error handling, safe resource cleanup, mocked HTTP contracts and
separate local Llama 3.2 3B installation/inference authorization. No P3-02 source
or live model integration has begun.

Existing expiry remains **23 October 2026, 23:59 EAT**. No production deployment or
real citizen/county data. All seven required checks, complete scanning, historical
records, logging protections and branch protection remain unchanged. No automatic
inheritance of Phase 2 acceptance or iterative-testing policy exception.

## Final owner decision applied

The owner explicitly approved f53e4aa6f904c8640d12cdca59ef177044ef498b and the exact
tested exposure above in P3-01 FINAL SECURITY APPROVAL AND PR PUBLICATION. The five
listed files are now updated; earlier proposal/pending language describes the prior
checkpoint. Phase 2 bytes are preserved with the recorded snapshot hash. Active
acceptance binds the unchanged baseline and expiry; no baseline/inventory, finding,
privilege/network, CI or ruleset changes. Publication and seven hosted checks are
authorized; no automatic merge, P3-02 source, live inference or production use.
