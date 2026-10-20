# P3-03B validation and conditional benchmark checkpoint

Prepared 20 October 2026. Issue #38. Tested source commit:
`85eac84d32f91387551c792379a6a9e6ca4ac698`.
Application exposure:
`d015b5cadfa07781d0f2eb063bb11bbd7dea923a684bad94a78dbae3506f476d`.
Protocol: [benchmark plan](P3_03B_BENCHMARK_PLAN.md).

## Authorized deterministic validation

Command: `backend/.venv/bin/python -m pytest backend/tests -m 'not integration' -q`.
Result: 336 passed, 79 PostgreSQL integration cases deselected, zero failures.
This includes 23 new sampling cases and the existing 313 backend unit/contract
regressions. Tests prohibit external socket connections and mock Ollama HTTP.
One existing Starlette/httpx deprecation warning; no dependency change made.
JUnit evidence: `/tmp/county-p303b-validation/backend.xml`.
Ruff lint/format, Mypy (48 source files), repository checks (347 files),
`git diff --check` and Gitleaks passed. No runtime source correction was needed.
Repository checker does not verify external URLs or render Mermaid.

## Security and artifacts

Packaging-only runtime build succeeded; no image application process was executed.
Changed backend image:
`sha256:d1e1251bbce123b908407b301ca43c3f9e244a9fe14fa403e8e9ba096a437a8d`.
Trivy 0.76.0 scan at 21:33 EAT: 44 HIGH, zero CRITICAL, zero fixable HIGH/CRITICAL.
Exact finding rows equal the previous hosted backend scan; complete runtime package
inventory validates against unchanged policy. No suppression/ignore configuration
was used. Fresh KEV retrieval retained catalog 2026.10.16; no reviewed findings match.
Scanner evidence is not proof of absence of exploitable application vulnerabilities.

Unchanged database/web evidence is reused from 20 October approximately 16:36 UTC:
database 71 HIGH/3 CRITICAL; web zero HIGH/CRITICAL. These images were not rebuilt
or rescanned here. Combined current/reused evidence totals 115 HIGH/3 CRITICAL.
The initial full-manifest scan setup could not use removed prior local image tags;
it generated no clean-scan claim. The changed backend was then scanned directly by
immutable image ID. Evidence: `/tmp/county-p303b-validation/scans/backend.json`,
`security-summary.json`, `kev.json` and `backend-scan.log` in its parent directory.

The owner actually confirmed review of all three CRITICAL assessments on 20 October;
that confirmation remains valid for this date only, not future daily reviews.
The security acceptance has not expired (23 October 2026, 23:59 EAT), but binds the
previous P3-03A exposure, not this sampling change. The unchanged policy correctly
fails: `Application/infrastructure exposure changed; owner review required`.
No acceptance, baseline, inventory, historical record or CI control was modified.

Both cached models' manifests and every referenced blob were rehashed successfully:

| Model | Manifest SHA-256 |
| --- | --- |
| llama3.2:3b | a80c4f17acd55265feec403c7aef86be0c25983ab279d83f3bcd3abbcb5b8b72 |
| qwen3:4b-instruct-2507-q4_K_M | 0edcdef34593eac1aa2be9c7d06c432dcf81945adca5eca2f27662c18f168ba0 |

Models evidence: `/tmp/county-p303b-validation/models.json`. No inference server
was started during this validation. Previous download server was loopback-only and
stopped. Available RAM was approximately 4.4 GiB; swap used approximately 1.63 GiB
of 2 GiB. Disk capacity remains ample. Benchmark cgroup enforcement and resource
headroom still require verification after the security gate clears.

## Conditional benchmark stopped

Zero live calls: zero of 96 scored calls and zero of six warm-ups. Therefore no new
English/Kiswahili semantic scores, abstention results, unsupported-claim findings,
truncation rates, latency percentiles, throughput or model-runtime memory measurements
exist. Previous model results remain historical; no improvement is inferred.
No blinded output package can be produced before actual authorized inference.
Independent bilingual review and the reviewed held-out set remain mandatory before
model selection. Neither model is selected; P3-04 live-generation readiness stays blocked.

The exact next decision is a separately documented, scoped P3-03B acceptance for the
tested exposure above, retaining all 118 existing findings, unchanged inventories,
expiry, daily actual human reviews and invalidation rules. Preserve prior P3-03A
acceptance byte-for-byte before replacing the active decision. Prepare the exact
record diff for owner approval; do not infer security-record approval from testing
or conditional inference authorization. No production, public service or real data.

No push, PR, merge, model download, acceptance change or live inference occurred
in this validation step. All seven required checks and branch protection remain intact.
