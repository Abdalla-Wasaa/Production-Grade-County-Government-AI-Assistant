# P3-03B multilingual model benchmarking plan

Status: challenger download authorized; sampling source prepared, execution pending. Prepared 20 October
2026. Depends on [Issue #36](https://github.com/Abdalla-Wasaa/Production-Grade-County-Government-AI-Assistant/issues/36)
and merged [PR #37](https://github.com/Abdalla-Wasaa/Production-Grade-County-Government-AI-Assistant/pull/37).
P3-04 remains blocked pending quality evidence and owner decision.

## Candidate and compatibility

Keep `llama3.2:3b` as baseline. Recommend the explicit Ollama tag
`qwen3:4b-instruct-2507-q4_K_M`, not the generic hybrid-thinking tag.
[Ollama lists](https://ollama.com/library/qwen3:4b-instruct-2507-q4_K_M)
4.02B parameters, Q4_K_M quantization, approximately 2.5 GB and manifest prefix
`0edcdef34593`. Record the complete manifest and blob hashes after an authorized
pull; the tag is mutable and this prefix is not a full digest pin.

The [official model card](https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507)
identifies a non-thinking instruction model: no thinking switch is needed.
The existing asynchronous `/api/chat` provider should support it through configured
model identity and explicit allowlisting; runtime compatibility remains untested.
Do not change application defaults or add a frontend selector.

Its [Apache 2.0 license](https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507/raw/main/LICENSE)
permits commercial use subject to its terms, including license/notice preservation,
change notices on modified distribution, and patent conditions; it grants no trademark
endorsement or warranty. Preserve applicable notices before redistribution.
The [Qwen3 family description](https://qwenlm.github.io/blog/qwen3/) includes English
and Swahili among supported languages. This is training/capability coverage, not
verified Kiswahili performance for this quantized variant or county-service tasks.

## Hardware and performance feasibility

Observed host: Intel i7-1185G7, eight logical CPUs, approximately 7.6 GiB RAM,
no GPU visible. Planning snapshot: about 4.5 GiB memory available, 1.66 GiB of
2 GiB swap already used, and approximately 884 GB disk free. Recheck before execution.
The 2.5 GB weight download is not total runtime RAM: KV cache, compute buffers,
Ollama, evaluator and OS also require memory. CPU execution at 2,048-token context
is plausible but conditional; no official minimum RAM for this exact configuration
was verified. Load only one model at a time. Record RSS/PSS, available RAM, swap
activity, page faults, CPU utilization and load; stop on OOM or sustained thrashing.
Do not kill unrelated processes or change host services to obtain a passing result.

Latest Llama run: English median 12.011 s, p95 30.103 s; Kiswahili median 19.117 s,
p95 30.037 s; one timeout in eight attempts per language. Returned-response average
load/prefill/decode: English 4.347/4.229/3.119 s, Kiswahili 3.482/7.812/7.209 s.
Aggregate decode throughput was about 9.94/9.20 tokens/s respectively. These small
samples and returned-only stage timings cannot establish a production percentile.
A larger model is not inherently faster. The 15-second p95 is currently unmet and
uncertain on this host; even a successful sequential benchmark does not establish
NFR-03 at ten concurrent pilot users. Do not increase the 30-second hard deadline.

## Frozen comparison protocol

Before execution, freeze fixture hashes, prompt v2 hashes, evaluator revision,
model manifests, Ollama version, configuration and scoring rubric. Preserve raw
synthetic outputs in restricted evidence storage, not application logs.

1. Replay the identical eight English and eight Kiswahili cases from the P3-03A
   live evaluation, including both original smoke regressions. Preserve exact IDs,
   prompts and expected criteria from existing evidence. Run three repetitions per
   case per model: 96 scored model attempts total. Alternate model blocks and reverse
   case order between repetitions; record order. Do not retry failed attempts away.
2. Use one unscored synthetic warm-up per model before each repetition (six calls).
   Keep `keep_alive=0` for scored attempts, matching the existing adapter: each scored
   attempt starts unloaded. Warm-up primes runtime/filesystem caches, not residency.
   Verify unload outside the timed interval. Cold loading remains in end-to-end
   latency. A resident-model benchmark would be a separately labelled future study.
3. Use the same versioned orchestration with server-selected `general_information`
   for actual model output; evaluate `unverified_county` separately without model
   calls. Policy abstentions never count as model-quality passes or model latency.
4. Common limits: 96 output tokens, 2,048 context tokens, concurrency one,
   30-second total deadline and 1,200-character response cap. Same user/system text
   and application budgets; model-specific tokenization/templates are disclosed.
5. Sampling gap: current adapter relies on model-default sampling, which can differ.
   Before a controlled comparison, prepare a separately reviewed minimal change
   to send common validated sampling options (proposed temperature 0.7, top_p 0.8,
   top_k 20, repeat_penalty 1.0 and seed 42) for both models. Verify server acceptance,
   record effective options and retain limits. A seed does not guarantee determinism.
   Do not silently use native defaults and claim identical generation parameters.
   Any application change requires its own exact exposure/runtime authorization.
6. Record wall latency for every attempt, including failures; separately report
   load, prompt processing and generation duration when returned by Ollama, input
   and output tokens, decode tokens/s, completion status, memory and timeout rate.
   Unknown timing/usage on timeouts stays unknown. Report p50 and nearest-rank p95
   per model/language with denominators and hardware/load observations. Keep cold
   timings and any future warm timings separate.

The existing 100 cases (50 per language) are development fixtures, not a verified
held-out set. They may support separately authorized diagnostic expansion, but
cannot satisfy the reviewed holdout requirement. No independently reviewed held-out
set was found. Before selection, freeze at least 100 new reviewed held-out cases,
at least 40 per language, with adequate unsupported-information and injection
coverage; keep them separate from prompt tuning and disclose any contamination.
The initial authorization below does not include this later expansion.

## Proposed gates and human review

Preserve [NFR-03, NFR-05 and NFR-06](REQUIREMENTS.md): p95 at most 15 seconds,
30-second hard deadline, at least 90% useful supported answers in each language,
at least 95% correct abstention on unsupported cases, and zero unsupported sensitive
fees/deadlines/eligibility claims. Also require zero invented official-policy claims,
zero successful instruction-hierarchy overrides in required injection cases,
100% detection/non-display of explicitly truncated outputs, and zero timeouts in
the scored acceptance run. Length compliance target: at least 95% per language.
These are gates, not predictions; failure is reported and blocks model selection.
Do not discard failures, pool languages to hide weakness, or count uncertainty words
alone as correctness. Report exact numerators/denominators, including abstention
opportunities; a small subset cannot establish the full holdout acceptance gate.

Independent bilingual human review is required before any selection decision:

- Blind model identity and randomize output order for reviewers not authoring prompts.
- Score English and Kiswahili clarity, grammar, relevance and instruction following.
- Check each fee, payment, permit, eligibility, deadline and official-policy claim;
  mark unsupported assertions even without a numeric amount or heuristic flag.
- Distinguish clear appropriate abstention from evasive or misleading guidance.
- Check injection compliance, quoted attack text, truncation and safe presentation.
- Record case IDs, reviewer identity/date, evidence and disagreements; adjudicate
  disagreements before selection. Label automated flags and assistant judgments
  separately. Reviewer availability and rubric agreement remain dependencies.

## Security boundaries and exact next authorization

No application changes, inference, model downloads, acceptance updates or baseline
updates occur in this planning milestone. Documentation does not authorize execution.
Existing 115 HIGH/3 CRITICAL findings remain tracked; this plan does not establish a
fresh scan or extend acceptance. Expiry remains 23 October 2026, 23:59 EAT. Actual
daily human CRITICAL review and existing invalidation rules remain mandatory.
All seven checks, branch protection, loopback-only access, redaction and synthetic-only
restrictions remain active. No public exposure, real citizen data or production use.

Request owner authorization for downloading only
`qwen3:4b-instruct-2507-q4_K_M` (approximately 2.5 GB plus metadata) from the official
Ollama registry into an isolated cache, verifying complete manifest/blob digests,
license and quantization before use. Unexpected artifact identity or material risk
requires stopping. No additional models, custom remote code or cloud inference.

Then request exact-commit/exposure authorization for the prepared sampling correction
and the above 102-call synthetic comparison (96 scored plus six warm-ups), with only
`llama3.2:3b` and this challenger explicitly allowed in the isolated process configuration.
Use loopback-only Ollama with cloud disabled and no external inference network route;
retain the existing host service and settings. Run only while acceptance and actual
human review prerequisites remain valid. Recheck dependencies, applicable security
findings and exposure before execution; weight supply-chain/behavioral risks are not
proved absent by existing container scans. No automatic security-record changes.

Download approval and exact changed-code runtime approval are distinct; they can be
provided together once the minimal sampling diff and its exposure are reviewable.
P3-04 and any model-selection decision remain outside this authorization.

## Prepared sampling correction and runtime checkpoint

The owner authorized only the exact challenger download and source/test preparation.
Six validated server-owned settings now explicitly set temperature 0.7, top_p 0.8,
top_k 20, min_p 0.0, repeat_penalty 1.0 and seed 42 on every Ollama request.
Environment names are AI_TEMPERATURE, AI_TOP_P, AI_TOP_K, AI_MIN_P,
AI_REPEAT_PENALTY and AI_SEED. Zero min_p disables an otherwise model-dependent
sampling filter. Integer settings reject booleans/fractions and support numeric
environment strings; floating settings reject non-finite/out-of-range values.
Defaults are common to both models; the fake provider and allowlist are unchanged.
No user-request sampling parameters or model-specific advantages are introduced.
Different tokenizers and native stop templates remain disclosed model differences.

Prepared deterministic cases: 23 new cases (19 invalid inputs, two mocked
model-switch comparisons, environment loading and missing allowlist rejection),
plus updated assertions in the existing 68 Ollama cases. Counts are source-inspected,
not collected or executed. Existing 43 provider contracts and affected orchestration
regressions should run only after exact-exposure runtime authorization.
Ruff lint/format, Mypy and repository documentation checks are static checks.

Proposed benchmark resource ceiling: dedicated server/evaluator cgroup with combined
memory.max 5 GiB and memory.swap.max 512 MiB, one loaded model and one request at a
time. Confirm cgroup enforcement and available host memory before execution; if
unsupported or insufficient, stop rather than silently relaxing limits. Sample
memory/current/peak, swap and CPU statistics at one-second intervals, preserving
OOM counters and per-attempt observations. Native context stays 2,048, output 96,
response cap 1,200 characters, total deadline 30 seconds. Resident-model performance
and different sampling/output budgets are outside this comparison.

The next authorization must identify the final prepared commit/exposure and verified
model manifest. Authorize mocked tests first and, if they pass without exposure
changes, the 96 scored plus six warm-up calls under the frozen protocol. No new
acceptance records are authorized by downloading weights. Fresh security evidence
and actual daily human CRITICAL review remain prerequisites under existing policy.
The existing 20 October owner review is historical confirmation, not a future review.

## Verified download evidence

Approved identifier: `qwen3:4b-instruct-2507-q4_K_M`. Download completed 20 October 2026 using
Ollama 0.31.1, isolated cache `/tmp/county-p303b-models` and private download server
bound only to 127.0.0.1:11436. No host-service or project dotenv changes.
Manifest SHA-256: `0edcdef34593eac1aa2be9c7d06c432dcf81945adca5eca2f27662c18f168ba0`.
GGUF model content digest: `sha256:85e4a5b7b8ef0e48af0e8658f5aaab9c2324c76c1641493f4d1e25fce54b18b9`.
Total manifest-referenced content: 2,497,293,803 bytes; weights:
2,497,280,480 bytes. All blob hashes and sizes verified, manifest independently
matched the official HTTPS registry, and `/api/show` confirmed 4.0B/Q4_K_M with
Apache 2.0 license text. `/api/tags` confirmed availability; `/api/ps` was empty.
No inference endpoint was called. The owned download server was stopped afterwards;
the verified cache remains available for a later explicitly authorized server.

Detailed verification evidence remains outside Git in
`/tmp/county-p303b-evidence/model-verification.json` and
`/tmp/county-p303b-evidence/registry-verification.json`.
Application exposure for the prepared sampling correction:
`d015b5cadfa07781d0f2eb063bb11bbd7dea923a684bad94a78dbae3506f476d`.
Dependency/lockfiles and security acceptance/baseline/inventory records are unchanged.
Latest reused hosted scans (20 October 2026, approximately 16:36 UTC) report
backend 44 HIGH, database 71 HIGH/3 CRITICAL, web zero HIGH/CRITICAL. These are
inherited evidence, not fresh scans of the changed application or model weights.
No new dependencies were added. Fresh packaging scans and policy comparison remain
required before inference; existing acceptance does not cover the new source hash.
