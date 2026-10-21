# Phase 3 conditional acceptance — restricted research foundation

Date: 21 October 2026. Status: **CONDITIONALLY ACCEPTED by explicit owner scope
amendment**; repository documentation closeout awaits owner review and merge.
The original assistant MVP is not fully accepted. This report adds no application,
model, inference or production authorization.

## Original and amended scope

The original [roadmap](ROADMAP.md), [requirements](REQUIREMENTS.md) and historical
[Phase 3 plan](PHASE_3_PLAN.md) require a bounded assistant MVP: provider adapter,
reviewed catalogue, bounded history, durable attempts/recovery, quota/usage ledger,
bilingual generation/source UI, FR-01..FR-10 and quality/load/failure evidence.

The owner's 21 October decision explicitly narrows closure to delivered providers,
bilingual prompt orchestration, benchmarking and evaluation research. The owner
states this is an amendment, not a claim that original criteria passed. See
[ADR 0005](DECISIONS/0005-phase-3-research-scope.md). Historical evidence and original
requirements are preserved; unfinished requirements remain mandatory in the backlog.

## Delivered features and historical evidence


| Deliverable | Merged PR | Merge commit | Existing evidence |
| --- | --- | --- | --- |
| P3-01 typed provider/fake | 31 | d66602dcd8c0ab46a33279ee7807b12954285ae8 | 43 provider and 128 regressions |
| P3-02 Ollama/configuration | 33 | d3dc9c1c4ce5e891c4cb9dd0b6bb99b565ca4892 | 68 mocked Ollama,43 provider,128 regressions |
| P3-03 bilingual orchestration | 35 | 94e63822990841290f84a7637827a10ee0305917 | 38 orchestration,111 provider,128 regressions,100 fake cases |
| P3-03A quality handling | 37 | 78ad0ae32b2c28f7d39e9ffe61843068d74ddab6 | 36 remediation,149 provider/orchestration,128 regressions |
| P3-03B benchmark/P3-03C investigation and certifi | 40 | 770f7be542ff33610ade77dfca1da43caae14734 | 336 regressions,79 PostgreSQL;96 scored calls plus6 warmups; review packet prepared |
| P3-03D Node toolchain | 42 | 2fc0ecfd895739eef3f026c2961c286c0a1397a8 | Node24.22.0/npm11.21.1;88 frontend;87 browser cases with one isolated successful retry;79 PostgreSQL and Compose evidence |
| Restricted renewal | 43 | 8332be908e19a23ec663a5ad6ccaada4dc4407fc | Exact-exposure approval and actual dated human security review |

Counts are reused historical suite evidence, not new runs or independent model-quality approval.
P3-03C investigation is delivered; its full issue acceptance remains incomplete.


Evidence: [provider guide](AI_PROVIDERS.md), [P3-03 assessment](P3_03_EXPOSURE_ASSESSMENT.md),
[P3-03A assessment](P3_03A_EXPOSURE_ASSESSMENT.md),
[benchmark report](P3_03B_BENCHMARK_REPORT.md),
[investigation](P3_03C_QUALITY_PERFORMANCE_REVIEW.md),
[Node remediation](P3_03D_EXPOSURE_ASSESSMENT.md) and
[security renewal](SECURITY_RENEWAL_2026_10_21.md). Preserved investigation evidence
hashes and sizes were reverified during scope review; raw outcomes were not rewritten.

## Deferred requirements and dependencies

All follow-ups are owned by Abdalla-Wasaa; no implementation is authorized by their
creation. [Issue #44](https://github.com/Abdalla-Wasaa/Production-Grade-County-Government-AI-Assistant/issues/44)
tracks the deferred assistant MVP and depends on the quality/performance gates in
OPEN [issue #39](https://github.com/Abdalla-Wasaa/Production-Grade-County-Government-AI-Assistant/issues/39).

| Original criterion | Unfinished work and unchanged completion gate | Tracking |
| --- | --- | --- |
| FR-03, NFR-04 | Reviewed generation contract/schema; durable attempts, idempotency, concurrent retry, cancellation/restart/recovery within 60s, deletion/replay tests | #44 |
| FR-07 | Owned bounded context; language continuity; expired/deleted exclusion; input budget 8,000 tokens and model context margin | #44 |
| FR-04/05/09 | Versioned reviewed synthetic cards, source/evidence-ID checks, expiry/withdrawal and no-match abstention; no fabricated guidance | #44 |
| NFR-07/08 | Before-dispatch per-user/global rate/concurrency/token reservations; bounded retry and reconciliation without duplicate charges/writes; content-free metrics | #44 |
| FR-06/08/09 | Bilingual accessible generation, source/limitation/abstention, pending/error/retry UI and browser evidence | #44 |
| NFR-05/06 | At least 100 reviewed held-out cases, at least 40/language; at least 90% useful supported answers and 95% correct abstention per language; zero unsupported sensitive claims; required injection/completeness safety | #39 and #44 final held-out gate |
| NFR-03/04 | Ten-user workload: non-AI p95 <=500ms, AI p95 <=15s, hard deadline 30s; transparent failure/recovery and limits evidence | #39 investigation and #44 integrated load |

The original initial-OpenAI assumption is reconciled with the later owner-approved
fake/Ollama implementation; an OpenAI adapter is separately approved future work.
Real county catalogue approval, privacy/provider-data/hosting decisions, public
accessibility and production security/recovery approval retain their existing
[pre-pilot gates](PRE_PILOT_GATE.md). They are not satisfied by this report.

## Known quality and performance failures

All 96 independent bilingual assessments remain pending (48 per language). No human
scores are fabricated; the repeated set does not meet the >=100 held-out gate.
Kiswahili quality has not passed. Neither model has selection/readiness approval.

| Model | English p95 / timeouts | Kiswahili p95 / timeouts |
| --- | --- | --- |
| Llama 3.2 3B | 24.44s; 1/24 | 30.01s; 7/24 |
| Qwen3 4B | 30.01s; 8/24 | 30.02s; 21/24 |

Both failed the unchanged 15-second p95 and benchmark zero-timeout gates. Policy
responses are not model-quality passes; fake evaluation does not prove factuality,
language quality or injection resistance. The eight-call cold/resident diagnostic
has not run. It may be deferred as an investigative method; latency acceptance
remains mandatory. P3-04 live generation remains blocked.

## Security binding and limitations

Reviewed main: 8332be908e19a23ec663a5ad6ccaada4dc4407fc (merged renewal PR #43).
Accepted exposure: 015755bffa0f038986d719624979b317cb5e5527dceed76447fd207d09747ab1.
Current expiry: **30 October 2026, 23:59 EAT** (20:59 UTC).
Runtime findings remain 115 HIGH / 3 CRITICAL; builder additionally 56 HIGH /
1 CRITICAL. These are image occurrences, not unique CVE counts. Latest recorded
review found no installed-package fixes or KEV matches; this documentation review
performed no new image scans and does not claim vulnerability-free software.

Actual owner CRITICAL review on 21 October covers SQLite CVE-2025-7458, libxml2
CVE-2026-6653 and both zlib CVE-2023-45853 occurrences. Future daily reviews must
actually occur. Historical acceptance snapshots, vulnerability inventories, daily
scans, invalidation rules, logging/privacy controls and least privilege are unchanged.
No automatic renewal, public Ollama, real citizen data or production deployment.
Live inference and changed exposure still require exact separate authorization.

## CI and closeout verification

Ruleset 25222082 retains all seven required checks bound to GitHub Actions app15368,
strict synchronization, resolved review threads, force-push/deletion restrictions.
Main and PR #43 have successful conclusions for backend-quality,
postgresql-integration, python-dependency-audit, frontend-quality,
compose-integration, repository-quality and secret-scan. At baseline inspection,
main secret-scan retained an inconsistent in_progress status despite success;
PR #43's checks were completed successfully. This is not a bypass.

For this documentation PR, local repository/link and CI-policy checks, diff/secret
checks and unchanged-exposure verification must pass. All seven fresh hosted checks
must pass on the published head before manual merge; baseline results are not
substitutes. The PR check rollup is the authoritative current hosted result.
No unaffected historical application suite was rerun locally solely for this report.

## Closeout and next planning boundary

Conditional acceptance applies only to the amended research foundation. Final
repository closeout requires the owner's manual merge of this protected PR with
seven successful checks and no blocking review. Issue #39 stays OPEN and assigned
to Abdalla-Wasaa; #44 preserves the unfinished original MVP. Neither is closed by
this documentation decision. Full MVP, live-generation and production acceptance
remain absent. After conditional closure, the next milestone is Phase 4 public
RAG planning: source ownership/provenance, ingestion threat model, retrieval and
citation evaluation design. No Phase 4 implementation is authorized.
