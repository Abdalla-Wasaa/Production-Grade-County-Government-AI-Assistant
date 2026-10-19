# P3-02 focused exposure assessment — authorized validation passed; owner records applied

## Prerequisites and exact source

PR #31 is owner-merged at d66602dcd8c0ab46a33279ee7807b12954285ae8. All seven
required PR checks passed; main was synchronized with --ff-only from a clean tree.
Its separate merged-main runs were still pending/in progress when inspected during
source preparation; do not claim a new green merged-main run. P3-01 acceptance
validated before source edits and remains byte-unchanged; it does not cover P3-02.
Issue #32 and the owner's explicit P3-02 authorization permit source implementation.

Branch: `feat/p3-02-ollama-adapter`. Application source is committed in a9c3420;
prepared mocked cases are committed in 426f486. Subsequent documentation commits do
not alter application exposure. Initial source preparation used static checks and packaging-only scans. The owner
subsequently authorized affcabe9503e009c9b2e613e9e9318b2d61e80d4 and the exact
exposure below for mocked synthetic validation. Actual results below supersede the
initial execution checkpoint. No model installation/download or live inference ran.

| Binding | Value |
| --- | --- |
| Prior approved P3-01 exposure | 54a7c2e7d075593f17107dd652edf035b28b7a399611f700c095bc5f1b04ecc4 |
| New P3-02 exposure | 8e1fa66f0928b01552045590813ad04f971c29a3c443dd92358721ccdc27a41d |
| Prior backend inventory | 119 packages; 7c9d236e62e9b96b9dfe7ca03dd92b1d999c6bacfb7fb8f67949a9790d88274e |
| New backend inventory | 122 packages; 3b313e4e52f23217faa9d0af79c3e339d2c4477aba1e6d66146dc1457c844aae |
| New backend image ID | sha256:7a99f7540bbce74f866f4e037141dbcdf18ae841505f9e90a89ab28415dac3e5 |

## Changes and newly introduced risks

Existing typed provider contracts and ManagedProvider semantics are unchanged.
The factory now selects fake or Ollama using validated server-owned configuration.
Default remains fake/fake-v1. Ollama uses explicit allowed models, initially
llama3.2:3b, through a bounded asynchronous /api/chat client. Configuration changes
can select another permitted model without editing domain/frontend code.

This introduces real new capability even with no new scanner findings: when opted
in and later authorized, prompts leave the backend process for a local inference
service; the HTTP parser/client, response validation, local service trust, optional
gateway credential, server logs/retention, model provenance and CPU/RAM/VRAM usage
require review. A compromised local service can return hostile data. The client
cannot prove a misconfigured local daemon will avoid cloud forwarding or logging.
No live model quality/resource claim follows from mocked tests or scans.

Controls: numeric 127.0.0.1/[::1] origins only; no DNS, userinfo, paths, query,
fragment, encoded host, redirect or ambient proxy/credential handling. TLS validation
remains enabled. Request-supplied endpoint/model overrides are absent. Allowlisted
explicit local model tags exclude cloud names. No discovery/download, retries,
provider fallback or tool dispatch. Output bytes/text/tokens, context, concurrency
and total deadline are bounded; model identity and response structure are validated.
Cancellation propagates and closes HTTP resources; server-side resource termination
still requires separate operational verification. Optional bearer key is SecretStr
and representations/logging avoid content/credentials. Server cloud disabling,
version/model manifests, log settings and loopback binding are prerequisites for any
future separately authorized live smoke test.

There is no new public API, authentication path, database schema/grant/query,
conversation mutation, frontend UI or Compose networking change. Startup/health
never probes or invokes Ollama. The existing SQLite CVE-2025-7458, libxml2
CVE-2026-6653 and zlib CVE-2023-45853 CRITICAL assessments remain tracked. This
adapter uses bounded Python JSON/HTTP parsing, not SQL/XML/SQLite or compressed
response processing; no additional direct path to those three defects was identified.
That focused assessment is not an exploit demonstration or proof of vulnerability-free
code. The owner's actual 19 October review is recorded separately; future daily
reviews remain mandatory, not automatically completed here.

## Dependency and complete scan evidence

HTTPX was already locked for development. Promoting it to runtime adds these exact
packages to the runtime image, with no resolved-version upgrades or removed packages:

| Runtime addition | Version |
| --- | --- |
| httpx | 0.28.1 |
| httpcore | 1.0.9 |
| certifi | 2026.7.22 |

[Dependency audit](security/p3-02/dependency-audit-summary.json) reports zero backend
and tooling advisories for the locked package sets. Python 3.12 compatibility is
resolved by the existing uv lock; actual adapter/runtime tests remain unexecuted.
No SDK or model-server dependency was added.

[Fresh scan summary](security/p3-02/scan-summary.json) and
[immutable manifest](security/p3-02/image-manifest.json) bind all three complete raw
reports, scanner/database freshness and the exact package/CVE comparison.

| Image | HIGH | CRITICAL | New/removed HIGH/CRITICAL occurrences | Available fixes / KEV matches |
| --- | --- | --- | --- | --- |
| Backend | 44 | 0 | 0 / 0 | 0 / 0 |
| PostgreSQL | 71 | 3 | 0 / 0 | 0 / 0 |
| Web | 0 | 0 | 0 / 0 | 0 / 0 |

Total 115 HIGH/3 CRITICAL remain exactly the inherited reviewed occurrence rows.
PostgreSQL and web full inventories/pins are unchanged; backend inventory changes
only by the three listed packages. No finding is suppressed, removed or reclassified.
No reported fixes or retrieved KEV matches; these are scanner facts, not assurance
that the new network code is flaw-free.

The unmodified normal policy scan correctly exits nonzero. Two distinct gates apply:
changed application exposure lacks an owner decision, and the backend inventory no
longer matches its approved 119-package reference. The scanner produced valid backend
JSON with a matching immutable image ID; the script's generic backend-evidence failure
label is caused by inventory validation, not a missing scan. No checker was weakened. Those initial policy failures preceded the separately approved record update below. Raw reports remain outside
source control with hashes in the summary.

## Authorized validation results

Owner authorization covered commit `affcabe9503e009c9b2e613e9e9318b2d61e80d4`
and exact exposure `8e1fa66f0928b01552045590813ad04f971c29a3c443dd92358721ccdc27a41d`.
All network behavior remained mocked; the existing socket-denial guard stayed active.
Actual 19 October results, from three separate invocations:

| Suite | Passed | Failed / skipped | Duration |
| --- | --- | --- | --- |
| Ollama HTTP/configuration/security contracts | 68 | 0 / 0 | 0.56 seconds |
| Existing provider/fake contracts | 43 | 0 / 0 | 0.27 seconds |
| Existing backend non-integration regressions | 128 | 0 / 0 | 3.05 seconds |

The existing 79 PostgreSQL cases were explicitly deselected; preserve their previous
passing provenance for unchanged SQL, migrations, grants and domain services. Do not
claim they were rerun. No correction was needed, so application exposure is unchanged.
Pre-existing Starlette TestClient/httpx deprecation warnings remain documented;
dependencies were not upgraded to silence them. Ruff lint/format, strict Mypy,
dependency audit and documentation/secret checks also pass.

[Validation summary](security/p3-02/validation-results.json),
[Ollama report](security/p3-02/ollama-results.xml),
[provider report](security/p3-02/provider-results.xml) and
[backend report](security/p3-02/regression-results.xml) preserve sanitized actual
results. Existing report validation accepts all three, with no failed/skipped cases.
They verify model switching, SSRF controls, safe error/log behavior, cancellation,
usage and cleanup using synthetic inputs only, not live-model quality or capacity.

The complete immutable scans above remain fresh for this exact source. Raw report
hashes, complete inventories, exact inherited rows and retrieved KEV evidence are
rechecked rather than repeating unchanged images for documentation-only updates.
No new HIGH/CRITICAL occurrence or reported fix is present. The three new runtime
packages and the loopback HTTP capability remain genuine reviewed deltas even when
scanner counts do not increase. No security records changed during testing; only the subsequently approved seven-file update below changes the active bindings.

## Owner-approved seven-file acceptance/publication update

Testing approval did not authorize policy records. The owner subsequently approved
the separate exact decision binding this tested exposure, exact new 122-package backend inventory and
the unchanged 118 individually enumerated inherited baseline occurrences.
Only the following seven files change under that explicit approval:

1. `.github/security-baseline.json`: update **only** backend `report_sha256` to
   `2440274bab03a5bf3794e35a63be14096baa939848e74cb36c5d4efbcba78ce5`,
   linking inventory provenance to the complete reviewed report. Resulting baseline SHA-256: `6616a2032aade6d2f0d4876c676601e1952abc51c2ddcfeb88447ff8cf8d85c8`. No finding row,
   severity, status, fix, image pin or other image baseline changes.
2. `.github/security-inventory.json`: update **only** backend source-report hash
   and inventory to 122 packages / SHA-256
   `3b313e4e52f23217faa9d0af79c3e339d2c4477aba1e6d66146dc1457c844aae`.
   The exact additions are httpx 0.28.1, httpcore 1.0.9, certifi 2026.7.22.
3. `.github/security-risk-acceptances.json`: separate P3-02 decision binding this
   tested exposure and resulting baseline bytes; same synthetic-only scope and
   expiry, no future exposure approval or finding expansion.
4. `docs/security/p3-02/p3-01-policy-snapshot.json`: preserve previous P3-01 baseline,
   inventory and active acceptance **bytes**, with file SHA-256s and raw UTF-8 strings
   whose re-encoding exactly reconstructs each original. Do not overwrite prior files.
5. `docs/P3_02_EXPOSURE_ASSESSMENT.md`: record actual owner decision and scope.
6. `docs/SECURITY.md`: document current restricted-development decision.
7. `AGENTS.md`: record that exact approved decision/publication scope; permanent rules
   and runtime-authorization procedure unchanged.

Current source record SHA-256s for the proposed byte-preserved snapshot:

| File | SHA-256 |
| --- | --- |
| .github/security-baseline.json | 0f48571f3b819b906b4aa78ce06c0beb4afd517283f78aad4e35c186d6056acf |
| .github/security-inventory.json | a68ff6b2805e4beba485590bb9459fd12cda89e1f20f4e62884c931db39e0c5d |
| .github/security-risk-acceptances.json | f406bd4555f22408b748411f4a15f002490fd9c118eea1bd4e24d6ade7e15f45 |

The owner decision must preserve 23 October 2026, 23:59 EAT expiry, daily actual human
CRITICAL reviews and all invalidation triggers: fix availability, new findings,
escalation, KEV listing and application/infrastructure/dependency exposure changes.
No suppression, reclassification, privilege/network expansion, CI/ruleset weakening,
automatic renewal or future exposure approval. Existing dated human review remains
honest and is not extended to later days.

The owner explicitly authorized this seven-file update **and** subsequent normal
commit/push, PR linked to #32 and all seven hosted checks. No automatic merge. The
prepared PR description records exact test provenance; hosted checks must pass before
merge readiness is reported.
Live model installation, download or inference is a different approval boundary and
is not included in this proposal. See the local guide for its prepared procedure.

Current expiry remains **23 October 2026, 23:59 EAT**. No real citizen/county data,
production credentials or production deployment. See the
[local guide](OLLAMA_LOCAL_DEVELOPMENT.md) for the separate server/version/model,
licence, resource and cloud-disabled prerequisites for future local Llama smoke tests.

## Owner decision application

Explicit P3-02 FINALIZE SECURITY RECORDS AND PUBLISH PR approval binds reviewed
commit 9b399b7be1cf76f98bdb24f502dbea876e7f54eb and the exact exposure above.
The complete seven-file diff was prepared and inspected before application. Old
policy bytes round-trip from the historical snapshot; only backend report provenance
and its three-package inventory delta change in the baseline/inventory records.
All inherited finding rows and severities, pins, other image inventories, expiry,
production prohibition and enforcement remain intact. This is not live-model
installation/inference approval. No automatic merge or future-exposure approval.
