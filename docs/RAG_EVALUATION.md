# RAG evaluation plan — thresholds proposed before execution

No evaluations, ingestion or live generation are authorized by this plan. These
criteria implement the existing Phase4 roadmap gate; new defaults require review
in P4-01. Keep retrieval, citation wiring and model semantics as distinct results.

## Reproducible evidence

Freeze synthetic document bytes, provenance, approval/revocation metadata, corpus
membership, chunker/tokenizer and embedding-space identity before held-out scoring.
Separate development/tuning from held-out sets. Independent bilingual reviewers
label relevance/answerability and acceptable page/span evidence before results are
seen. Use at least50 relevant queries per language for retrieval, plus at least20
unsupported/ambiguous queries per language and multilingual injection/lifecycle
cases. Report cross-language and mixed-language slices separately. Repeated cases
or translated duplicates must be disclosed, not inflated as independent samples.

Fake embeddings/responses verify contracts and determinism only; they do not prove
semantic recall or groundedness. Real embedding/model runs require model/license,
resource/dependency/security and exact runtime approvals. CI stays offline with
synthetic vectors, fake providers and mocked network transport; real pgvector
integration uses separately approved disposable PostgreSQL, not SQLite substitutes.

| Gate | Metric and acceptance | Evidence |
| --- | --- | --- |
| Retrieval relevance | Recall@5 >=0.85 independently for en/sw on >=50 relevant held-out queries/language; macro average relevant evidence units retrieved / labelled relevant units; also report success@5 and MRR, no-relevant queries separately | Query/case IDs, gold chunk/span labels, retrieved IDs/scores, corpus/space identity; compare lexical baseline |
| Source filtering | Zero unauthorized, unapproved, expired, wrong-county/space, revoked or deleted source content in results/caches/prompts; test before and during requests and restore | Adversarial DB/API and race/recovery tests |
| Citation integrity | 100% citation IDs resolve to selected currently eligible immutable version/page/span; zero invented IDs/URLs or withdrawn-content exposure | Deterministic validator tests; link policy and citation resolution checks |
| Grounded semantic claims | Zero unsupported sensitive fees/deadlines/eligibility/official-policy claims; >=95% of independently reviewed substantive claim units supported by cited evidence per language (proposed additional gate) | Human claim/span support labels; factual existence of source alone is insufficient |
| Answer/abstention quality | Preserve NFR-05: >=100 independently reviewed held-out cases, >=40/language, >=90% useful supported answers and >=95% correct abstention per language; record each denominator | Independent review with identity/date, adjudication and blinded/frozen submissions; #39 remains incomplete |
| Injection/completeness | Zero successful hierarchy override/exfiltration or silent truncation in required reviewed cases; report policy versus model responses separately | Direct/indirect bilingual injection, forged citations, hidden content, truncated/timeout output cases |
| Performance | Proposed retrieval-only p95<=500ms at10 authenticated concurrent users over10,000 synthetic chunks; measure cold/warm query embedding separately and end-to-end, not just SQL | Named hardware, dataset, index/space, timeouts, CPU/RAM/swap, query plans and raw attempts; owner review before use as a gate |
| Overall generation | Existing NFR-03 AI p95<=15s, hard deadline30s; report timeout/error rates and incomplete outputs, no raised deadline to pass | #39/#44 still block live integration; retrieval speed cannot prove generation speed |
| Resource/isolation | Parser hard limits from reviewed contract; query/ingestion concurrency and token caps; zero OOM and unauthorized network/secret access in required tests | Measured process/cgroup CPU/RAM/swap, bounded job/retry evidence and enforced limits |
| Lifecycle | Failed ingestion never publishes; idempotent repeat/concurrent jobs; atomic activate/rollback; immediate revocation exclusion and verified purge/restore replay | Operator grants, DB transactions, forced failure and cancellation tests |

Unsupported-answer refusal is evaluated at two boundaries: deterministic no-evidence
policy without dispatch, and human-reviewed model abstention with evidence present
but insufficient/conflicting. Never count the first as a model-quality pass. Report
all case failures/timeouts; preserve raw sanitized evidence rather than replacing
failed outputs with policy answers retrospectively.

## Test and monitoring matrix

- Unit/contracts: file/type/metadata/request limits, normalization offsets, chunk
  boundaries, dimension/NaN rejection, citation membership, error redaction and budgets.
- PostgreSQL: migrations/constraints/least privilege, exact filtered ordering,
  corpus/space isolation, concurrent jobs/activation, revocation races and purge/restore.
- Security: malicious PDF/active content, missing scanner evidence, resource exhaustion,
  traversal/symlinks, unauthorized operators, forged IDs/SQL, indirect injection,
  source URL policy/SSRF if later enabled, secret/log and sensitive-data checks.
- Frontend/API: existing auth/history/privacy regression suites; no new generation
  UI or endpoint until #44 contracts and implementation approvals. Citation rendering
  uses safe text/URLs and preserves accessible bilingual failure states.
- Operations: quarantine cleanup, job leases/deadlines, partial batch rollback,
  corpus activation rollback, stale review/expiry, metric redaction and runbook replay.
- CI: backend-quality, postgresql-integration, python-dependency-audit,
  frontend-quality, compose-integration, repository-quality and secret-scan stay mandatory.

Record traceable release/space/model/prompt versions; per-language attempts/returns,
policy-handled versus model-generated counts, hits/misses, citation failures,
timeouts/truncations, p50/p95, embedding/provider usage and resource peaks. Operational
metrics exclude query/content/vector text and credentials. Alert on rejected files,
scanner staleness, overdue source review, purge backlog, retrieval failures and
resource limits. Publish no real-data diagnostics.

## Acceptance authority and limits

Source owner approves each released version; independent bilingual review establishes
semantic evidence; repository owner reviews exact security/exposure and acceptance.
New findings/fixes/KEV/severity/inventory/isolation changes invalidate applicable
acceptance. Green CI does not override those decisions. Current findings remain
runtime115 HIGH/3 CRITICAL plus builder56 HIGH/1 CRITICAL; no new scan is claimed here.
Current expiry is30October2026 23:59EAT with daily actual CRITICAL reviews required.
No renewals, model selection, #39 closure, production or real-data approval follows.
