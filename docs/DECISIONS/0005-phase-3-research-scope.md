# ADR 0005: Conditional closure of the Phase 3 research foundation

Date: 21 October 2026. Decision: explicitly owner approved; documentation PR review
and merge pending. Scope: documentation and tracking only.

## Context

The original [roadmap](../ROADMAP.md) Phase 3 described a bounded assistant MVP:
FR-01..FR-10, durable attempts/recovery, catalogue, bounded context, usage limits,
generation UI and independent quality/load evidence. Provider/orchestration research
is delivered, but those full exit criteria are not met. Closing all original work
or treating a green CI run as model-quality acceptance would misstate the evidence.

## Decision and owner authorization

The owner explicitly approved: “formally narrowing Phase 3 closure to the delivered
AI provider, bilingual prompt orchestration, benchmarking and evaluation-research
foundation” and “CONDITIONALLY ACCEPTED for restricted synthetic development only”.
This is an amendment to scope, not a claim that original MVP criteria were satisfied.
The same decision authorizes this focused documentation branch/PR and normal CI.
No additional security/publication waiver is needed for these unchanged-exposure
documents under that explicit owner instruction. Owner merge remains required.

Preserve the original roadmap row and implementation sequence. Carry unfinished
MVP work into [issue #44](https://github.com/Abdalla-Wasaa/Production-Grade-County-Government-AI-Assistant/issues/44),
owned by Abdalla-Wasaa, with original requirement IDs and measurable gates.
Reuse OPEN [issue #39](https://github.com/Abdalla-Wasaa/Production-Grade-County-Government-AI-Assistant/issues/39)
for independent bilingual quality and latency. Neither is considered completed by
this decision. Fake/Ollama reflect the later approved provider implementation;
OpenAI remains future separately approved adapter work.

## Consequences and alternatives

The amended research foundation may close conditionally after reviewed merge.
Full MVP acceptance, model selection, Kiswahili quality and latency remain blocked.
The eight-call diagnostic is a possible investigative method, not a mandatory way
to obtain the still-mandatory performance evidence. The 96 pending assessments
remain required under issue #39 and do not satisfy NFR-05's held-out denominator.

Rejected alternatives: claim full MVP acceptance; erase unfinished requirements;
relax quality/latency gates; force an inference experiment for paperwork completion.
Retaining the original phase open was the default before the owner's scope decision.

Phase 4 planning may begin after conditional closure. Implementation/RAG needs
separate approval; the original phase dependency is amended for planning only.
No P3-04 live generation, application changes or inference are authorized here.
No security records, inventories, historical evidence or runtime controls change.
Development remains synthetic-only through 30 October 2026, 23:59 EAT under the
existing exact-exposure decision, daily actual CRITICAL review and invalidation
conditions. No public Ollama, real citizen data or production deployment.

See the [acceptance report](../PHASE_3_ACCEPTANCE.md) for delivered evidence,
remaining requirements, security binding and review/merge conditions.
