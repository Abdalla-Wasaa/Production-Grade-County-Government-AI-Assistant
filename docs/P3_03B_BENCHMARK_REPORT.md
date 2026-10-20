# P3-03B comparative benchmark report

Completed 20 October 2026. Issue #38. No model selected; P3-04 remains blocked.

Running commit: `bd7f9e2fc124ab5c0317caf8712e5059dac563d1`.
Exposure: `d015b5cadfa07781d0f2eb063bb11bbd7dea923a684bad94a78dbae3506f476d`.

## Security decision and execution

The owner explicitly authorized the minimum scoped acceptance and conditional workload.
[Assessment](P3_03B_EXPOSURE_ASSESSMENT.md) documents the five-file decision.
Previous P3-03A approval bytes are preserved unchanged. Acceptance/policy evaluation
now passes for the running exposure, exact inventories and all 118 inherited findings.
Expiry stays 23 October 2026, 23:59 EAT. Actual owner CRITICAL review was confirmed
for 20 October; no future daily review or production approval is inferred.

336 deterministic tests passed before inference. Changed backend scan: 44 HIGH,
zero CRITICAL, zero reported available fixes/KEV matches, exact unchanged inventory.
Unchanged reused database/web evidence retains combined 115 HIGH/3 CRITICAL.
No suppression, privilege expansion, application edits, additional downloads or
security-policy weakening occurred during the benchmark.

## Protocol and provenance

Exactly 96 scored calls (24 per model/language) and six separate warm-ups completed.
The isolated server log independently contains exactly 102 POST /api/chat requests.
Zero policy-handled responses were included: actual model calls used the approved
general-information policy; no policy abstention is counted as a model-quality pass.
Each eight-case language set ran three times, so these are repeated diagnostic cases,
not 24 independent questions or a new held-out benchmark. Independent review is pending.

Run interval: 2026-10-20T18:39:48.444995+00:00 to 2026-10-20T19:22:20.710621+00:00.
Identical prompt v2, sampling (0.7/0.8/20/0/1/42), context 2048, output 96,
character cap 1200 and 30-second deadline. Keep-alive zero; every scored call began
unloaded. Warm-ups prime runtime/filesystem caches but do not establish residency.
Model order: Llama/Qwen, Qwen/Llama, Llama/Qwen; second repetition reverses cases.
Native model templates/tokenizers remain different; a fixed seed is not a guarantee
of bit-for-bit deterministic output. Record hashes and model digests are in the evidence.

## Automated results

| Model | Language | Returned / attempts | Complete | Timeout | Truncated / suspected | p50 s | p95 s |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Llama 3.2 3B | en | 23/24 | 23 | 1 | 0 / 0 | 13.765 | 24.438 |
| Llama 3.2 3B | sw | 17/24 | 11 | 7 | 3 / 3 | 23.170 | 30.006 |
| Qwen3 4B Instruct | en | 16/24 | 16 | 8 | 0 / 0 | 21.863 | 30.010 |
| Qwen3 4B Instruct | sw | 3/24 | 3 | 21 | 0 / 0 | 30.008 | 30.016 |

Timeout rates: Llama en 4.2%, sw 29.2%; Qwen en 33.3%, sw 87.5%.
Latency includes every scored attempt, including timeouts; p50 is the median and
p95 the nearest-rank percentile. Small wall-clock overruns around 30.01 s reflect
deadline/error-processing overhead, not a relaxed deadline. No unexpected provider
error other than timeout occurred. All returned outputs fit the character cap:
Llama en 23/23, sw 17/17; Qwen en 16/16, sw 3/3. Against all attempts, counts are
23/24, 17/24, 16/24 and 3/24. Character compliance is not sentence-following quality.

Llama sw had three explicit token-limit truncations and three suspected incomplete
permit outputs. All are non-displayable under the existing status policy. Qwen had
no returned incomplete outputs; its 29 timeouts cannot be classified as complete.

## Semantic and safety limitations

Automated uncertainty signals on expected cases: Llama en 12/15, sw 0/15;
Qwen en 7/15, sw 0/15. These are regex signals with failures retained in denominators,
not independently reviewed correct-abstention rates. For example, a Llama Kiswahili
service response states that verified county information is unavailable despite the
heuristic not matching it. Missing a signal does not prove absence of uncertainty.

Qwen has three numeric-fee flags, all en-injection-01 repetitions. Assistant inspection
shows explicit refusal quoting the fictitious KES 750 amount, not assertion of that
fee. Do not count these flags as confirmed hallucinations. Llama had no automatic
claim flags, yet its Kiswahili injection answer says no payment is required; that
is a potential unsupported no-fee assertion requiring independent contextual review.
Its permit responses are off-target and its ambiguity answer is not a useful
clarification. Qwen’s returned Kiswahili smoke response has unclear grammar/meaning.
These are assistant observations, not completed independent bilingual scoring.

Neither zero flags nor uncertainty words prove truth. Successful injection override,
unsupported official guidance, appropriate abstention and useful supported answers
remain pending blinded independent review; no semantic pass rate is claimed.

## Performance and resources

| Model/language | Mean load s | Mean prompt processing s | Mean generation s | Decode tokens/s |
| --- | --- | --- | --- | --- |
| Llama/en | 5.834 | 5.498 | 3.087 | 7.51 |
| Llama/sw | 4.228 | 9.139 | 8.319 | 7.70 |
| Qwen/en | 8.221 | 6.405 | 5.308 | 6.62 |
| Qwen/sw | 6.775 | 10.636 | 4.820 | 6.15 |

Stage means and throughput cover returned responses only; timeout token usage and
stage durations are unknown. They are survivor-biased and do not explain every
failed attempt. Full metadata preserves observed tokens and per-attempt timing.

CPU-only i7-1185G7, eight logical CPUs, Ollama 0.31.1. Combined cgroup memory ceiling
5 GiB and swap ceiling 512 MiB were verified. Kernel-observed peak was approximately
4.65 GiB; one-second sampled peak was 4.64 GiB. Sampled cgroup swap peaked near
47.2 MiB. No memory.max, OOM or OOM-kill events, and no sustained-thrashing stop
condition occurred. Host available RAM fell to about 2.04 GiB, and host free swap
briefly reached zero: headroom was limited, not comfortably provisioned. Cgroup
CPU usage was approximately 7,405 CPU-seconds across the 42.5-minute run, about
2.9 logical CPUs on average. No GPU or CPU quota was used.

Load/prefill/decode costs and slow CPU token generation all contribute. Later-run
latency varied: Llama English smoke 12.640/24.438/17.589 s across repetitions.
Thermal throttling and frequency were not measured, so no thermal root cause is
asserted. Balanced order reduces but does not eliminate host drift and cache bias.
Neither model meets 15-second p95 here; this sequential cold benchmark also cannot
establish the ten-user pilot performance requirement. No timeout threshold was raised.

## Gates, review and recommendation

Both models fail the p95 and zero-timeout gates. Llama also returns incomplete
Kiswahili output. Independent language/usefulness/abstention/injection review and
at least 100 reviewed held-out cases remain absent. Character-limit compliance
alone is insufficient. No model is approved for official county guidance.

Keep P3-04 live-generation integration blocked. Retain Llama only as the existing
restricted research baseline; Qwen is not demonstrated to be a viable replacement
under this host and budget. Independent review may clarify its returned-output
quality but cannot remove observed latency/timeouts. Before another benchmark,
decide whether representative hardware is available; do not silently change budgets
or download another model. Any material change requires the established approval.

Reviewers should use [blinded outputs](security/p3-03b/blinded-review.json), score
English and Kiswahili independently, document identity/date/rationale and adjudicate
disagreements. Model labels/timings are omitted; style or failure patterns may still
make identity inferable. The private unblinding key remains outside Git until review.

## Evidence and cleanup

[Metadata](security/p3-03b/benchmark-metadata.json),
[summary](security/p3-03b/benchmark-summary.json),
[evidence hashes](security/p3-03b/evidence-manifest.json),
[exact harness](security/p3-03b/benchmark-harness.txt),
[launcher](security/p3-03b/benchmark-launcher.txt) and
[summary/review tooling](security/p3-03b/benchmark-summary-tool.txt) preserve the run.
External evidence is under /tmp/county-p303b-benchmark; paths/hashes are recorded.
The evidence harness has environment-specific paths; reproduce only with approved
models/exposure and a new authorization where required, not by running blindly.

The owned transient unit exited successfully and its server stopped. No loaded
benchmark model remains. Existing host Ollama service was not modified. Full prompt
and answer strings were absent from captured application and server logs; this is
a bounded log-content check, not proof of universal leakage prevention. No further
application edits, security-record changes, push, PR or merge occurred after the
scoped acceptance. Publication remains subject to the established review workflow.
