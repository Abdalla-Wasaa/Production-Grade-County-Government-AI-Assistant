# P3-03C bilingual review and inference performance investigation

Tracking: [Issue #39](https://github.com/Abdalla-Wasaa/Production-Grade-County-Government-AI-Assistant/issues/39).

Status: independent review prepared, not submitted; no new inference. Related
[Issue #38](https://github.com/Abdalla-Wasaa/Production-Grade-County-Government-AI-Assistant/issues/38),
[Issue #36](https://github.com/Abdalla-Wasaa/Production-Grade-County-Government-AI-Assistant/issues/36)
and [PR #37](https://github.com/Abdalla-Wasaa/Production-Grade-County-Government-AI-Assistant/pull/37).

## Evidence integrity and reproducibility

Reviewed P3-03B commit `975e05401f02d3832a87a861b07b0882f4eb91af` and unchanged exposure
`d015b5cadfa07781d0f2eb063bb11bbd7dea923a684bad94a78dbae3506f476d`.
[Original report](P3_03B_BENCHMARK_REPORT.md), [plan](P3_03B_BENCHMARK_PLAN.md) and
[96 blinded outputs](security/p3-03b/blinded-review.json) remain unchanged.
All nine original evidence-manifest entries exist and match their exact byte sizes
and SHA-256 hashes. There are 96 scored outputs plus six separate warm-ups,
102 server chat requests, three repetitions of eight questions per language/model,
and 2,404 one-second resource samples. No raw failures or outputs were discarded.

Original metadata, harness and summaries were already tracked; raw resources,
synthetic answers and logs depended on ephemeral /tmp storage. Byte-identical copies
now live under docs/security/p3-03c/evidence, with original fixture and baseline
inputs needed by the preserved harness. [Integrity record](security/p3-03c/evidence-integrity.json)
binds those copies. Private unblinding key remains outside Git, hash-bound by the
original manifest, with a 0600 durable coordinator copy at
/root/.local/share/county-ai/review-keys/p3-03b-private-review-key.json. The parent
directory is 0700. Owner-managed encrypted backup/access remains a handover task;
never include this key in reviewer packets or the PR.

The preserved harness has absolute local paths and requires compatible Ollama,
approved weights, Python environment, Linux network/cgroup controls and source revision.
Reproduction means reconstructing that environment from recorded versions/digests and
fixtures; seed 42 does not guarantee identical generated text. /tmp-only paths should
be staged from the durable copies by a coordinator after separate execution approval.
No portability run, new inference or model download was performed in P3-03C.
Original hardware counters cannot be recreated retrospectively.

## Independent review handover

Provide only the [reviewer guide](security/p3-03c/review/REVIEWER_GUIDE.md),
[English CSV](security/p3-03c/review/en-review.csv) and
[Kiswahili CSV](security/p3-03c/review/sw-review.csv) to reviewers. Each contains
48 output rows with stable Bxxx review IDs and case IDs; all human fields are blank.
Do not provide the whole repository: model-labelled raw metadata can defeat blinding.
No model identities or timings are in the reviewer packet. Preserve original blinded
JSON; CSV formula escaping changes only spreadsheet presentation, not source evidence.
CSV round-trip checks verified row counts, unique IDs and blank assessment fields.

The rubric covers semantics, language, usefulness, abstention, unsupported fees and
procedures, fabricated regulations, injection, completeness, instructions and safety.
Actual independent bilingual reviewer identity/pseudonym, date, decisions and notes
are required. Two reviewers plus independent adjudication are recommended; none has
submitted results. Automated flags and prior assistant observations are not human
judgments. Freeze review submissions before unblinding. This repeated diagnostic set
does not satisfy the at-least-100-reviewed-held-out requirement in NFR-05.

## Observed performance and attribution limits

Existing results remain: Llama en/sw p95 24.44/30.01 s with 1/24 and 7/24 timeouts;
Qwen en/sw p95 30.01/30.02 s with 8/24 and 21/24 timeouts. Both fail the unchanged
15-second p95 and zero-timeout gates. No independent model-quality score is available.

| Observation | Evidence | Supported conclusion and limit |
| --- | --- | --- |
| CPU utilization | Host cumulative CPU counters: 38.17% busy across eight logical CPUs, 1.31% iowait; benchmark about 2.9 logical CPUs average | CPU inference is costly, but full-host saturation is not established. Per-thread utilization, frequency, thermal, memory-bandwidth and cache counters were not captured. |
| RAM/swap | Host available RAM minimum about 2.04 GiB; zero free swap in 352 of 2,404 samples; host swap-in 14,923 pages and swap-out 113,332 pages (4 KiB pages: 58.3/442.7 MiB) | Real memory pressure occurred. Host counters include unrelated workloads; causal per-model latency attribution is unproven. No sustained-thrashing stop threshold fired. |
| Cgroup limits | RAM ceiling 5 GiB, swap ceiling 512 MiB; sampled peak about 4.64 GiB RAM/47.2 MiB swap; no max/OOM events | Resource limits held without observed OOM. Cgroup memory includes cache/children; it is not model-only RSS or VRAM. |
| Model loading | Returned-only mean Llama load en/sw 5.83/4.23 s; Qwen 8.22/6.77 s | Loading consumes substantial budget; model-size/cache effects plausible, not isolated experimentally. |
| Prompt processing | Returned-only means Llama 5.50/9.14 s, Qwen 6.40/10.64 s | Kiswahili tokenization/prefill is more expensive in observed returns; tokenization and workload differ, not proof of a general language penalty. |
| Generation | Returned-only decode about 7.51/7.70 tokens/s Llama, 6.62/6.15 Qwen | Low throughput contributes to deadline pressure; timeout token counts/durations remain unknown. |
| Model/context settings | Both Q4_K_M, context 2,048, output cap 96, one request/model, 30 s deadline | No context-size or quantization sweep was run. Cap can truncate output, but the optimal budget and its effect are unmeasured. |
| Cold versus warm | keep_alive=0; every scored call begins unloaded; one unscored warm-up per model/repetition | Warm-ups may prime OS/runtime caches; no resident warm-start benchmark exists. Do not infer a measured warm-start benefit. |

Timing means exclude timeouts and are survivor-biased. End-to-end percentiles include
all scored attempts. Workload is sequential, not the ten-user pilot. Native templates
and tokenizers differ even with common parameters; lower Qwen throughput and larger
weights do not establish which internal component dominates without profiling.

Repetition medians across both languages show variability: Llama 14.42/26.46/18.74 s
and 0/7/1 timeouts; Qwen 30.00/30.01/24.18 s and 9/14/6 timeouts. Balanced order helps
but does not remove host-load, cache and thermal confounding. Thermal throttling is
only a hypothesis. More RAM, warm residency and GPU acceleration are hypotheses for
future experiments, not measured improvements. Raising deadlines is not remediation.

## Hardware options and cost considerations

All sizes below are engineering planning estimates for these 3B/4B Q4 models at
2,048 context and concurrency one, not vendor-certified minimums or latency promises.
No purchase, rental, driver installation or host change is authorized here.

| Option | Practical planning floor | Performance risk | Operations and cost | Security |
| --- | --- | --- | --- | --- |
| A: current CPU host | Existing eight logical CPUs, about 8 GiB RAM, single-model enforced limits and disk headroom | Observed p95 failure, swap pressure, CPU throughput and cold loads remain; suitable for offline research, not a performance-approved service | No new hardware spend; substantial developer time, power and opportunity cost; isolate competing workloads without killing unrelated processes | Existing local synthetic boundary; do not publicly expose service or relax limits |
| B: more RAM | Compatible host with at least 16 GiB RAM, preferably 32 GiB for backend/DB/tools alongside one model; retain CPU baseline | More headroom may reduce swapping; cannot solve compute/prefill or language limitations by itself | Moderate one-time upgrade or replacement; verify whether this laptop/VM RAM is upgradeable before procurement; no supported upgrade path assumed | Recheck OS/driver/firmware, encrypted model/evidence storage and access controls; changed environment needs assessment |
| C: GPU development host | At least 16 GiB host RAM and supported discrete GPU with at least 8 GiB VRAM as a trial floor; prefer 12+ GiB VRAM and 32 GiB host RAM for headroom | Must verify full offload, actual VRAM fit, driver compatibility and measured p95; context/concurrency increases can exceed memory | Highest up-front cost, power and driver complexity; rental adds recurring compute/storage/egress and requires owner budget/region approval; obtain current quotes rather than assume prices | New driver attack surface and potentially remote host; private access, no public Ollama, least privilege and storage cleanup. Cloud hosting is a separate security decision, not an approved external inference API |

[Ollama hardware support](https://docs.ollama.com/gpu) documents supported GPU/driver
combinations; check the actual device before purchase. [Ollama FAQ](https://docs.ollama.com/faq)
documents memory/context, residency and parallelism controls. These support planning,
not a promise of 15-second p95 on any proposed host. Existing approved loopback-only
provider means remote-host access cannot be silently enabled by widening its URL rules.
Use a reviewed local execution environment or separately approved connectivity design.

## Minimal next experiment, not authorized execution

First obtain blinded human review and pick a representative hardware budget. Then
propose a separately authorized inference-performance diagnostic: same two digests,
same prompts and limits, no more model downloads; collect per-process/thread CPU,
frequency/thermal data if exposed, RSS/PSS, page faults, IO and GPU offload/VRAM if
applicable. Compare cold and explicitly warm-resident trials separately, preserving
the existing cold baseline and checking whether memory pressure correlates with
per-attempt timing. Any change to keep_alive, runtime limits, host or adapter source
requires a reviewed plan and applicable runtime/exposure approval before execution.
Keep CI fake/mocked. Do not begin P3-04, extend timeouts or select a model now.

## Expiry and renewal decision package

Current accepted exposure and all 118 inherited occurrences remain unchanged.
Expiry: 23 October 2026, 23:59 EAT (20:59 UTC). Owner's actual 20 October CRITICAL
review remains historical only. Future daily reviews must actually occur. No risk
record, baseline, inventory, date or security-control change is part of P3-03C.

Before continued runtime beyond expiry, assemble a new owner decision with:

- Exact source commit/exposure, both immutable model digests, host/resource/network
  configuration, complete current inventories, image IDs and current full scans.
- Individually identified accepted CVE/package occurrences, fixes, severity changes,
  KEV/exploitation evidence, exposures and controls. Do not assume counts stay 118;
  new or newly fixable findings invalidate the old decision and require resolution.
- Fresh actual human review of all CRITICAL assessments: SQLite CVE-2025-7458,
  libxml2 CVE-2026-6653 and zlib1g CVE-2023-45853. No fabricated or predated review.
- Explicit owner-selected start/end, synthetic local scope, accountable owner and
  residual-risk rationale; current policy caps an acceptance period at 30 days.
  This document proposes no new expiry or automatic grace period.
- Proposed exact record diff and byte-preserved snapshot, unchanged production ban,
  daily reviews, fix/new-finding/severity/KEV/exposure/dependency invalidation, full
  scans, seven CI checks and protected PR review. Confirm the new decision normally
  passes policy; do not disable expiration or weaken enforcement to continue.

If no new valid decision exists at expiry, stop runtime/inference requiring it.
Do not treat publication approval, a draft renewal or review submission as renewal.
Production and real citizen data remain prohibited even if development is renewed.

## Publication checklist and exact owner decisions

P3-03C is documentation/evidence only; app exposure is unchanged. AGENTS requires
separate decisions before publication; its latest P3-03B authorization explicitly
excludes automatic publication. Owner should authorize pushing this evaluation
branch and opening a PR linked to the new tracking issue and #38, covering the
unpublished P3-03B sampling change, approved five-file acceptance and all evidence.
This branch currently includes those unpublished ancestor commits; disclose the
full diff against main. Do not publish the private unblinding key. Review packet
must be distributed separately from model-labelled coordinator evidence.

No new security-record approval is needed merely to publish these docs while the
exact accepted exposure/conditions remain valid. Do not expand acceptance to new
runtime, hardware, models or dates. Seven hosted checks must run normally after
publication; none was bypassed or claimed as passed for this unpublished branch.
No PR/merge, new app feature, inference, renewal or real data is authorized here.
