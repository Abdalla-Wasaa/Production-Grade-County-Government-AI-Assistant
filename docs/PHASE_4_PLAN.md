# Phase 4 public-document RAG plan — planning only

## Verified prerequisite and authorization

Phase3 closure PR #45 is merged at d3a6b06e9a4a40b1141f30938e7d1fcd4b89b24a.
Main was synchronized with git pull --ff-only from a clean working tree. All seven
checks on PR45 completed successfully. ADR0005 and PHASE_3_ACCEPTANCE.md are present
on main: conditional acceptance applies only to the amended research foundation.
Issues #39 and #44 remain OPEN and owned by Abdalla-Wasaa. Original MVP criteria
were preserved, not passed. See [acceptance](PHASE_3_ACCEPTANCE.md) and
[ADR0005](DECISIONS/0005-phase-3-research-scope.md).

The owner explicitly authorizes this planning branch, issue creation and one
planning PR with all seven hosted checks. No Phase4 implementation, source ingestion,
model download or changed-runtime execution is authorized. No new ADR is needed:
this elaborates the existing modular-monolith, exact-search and source-approval
architecture. Contract decisions remain proposed until owner review.

## Architecture and mandatory first release

Reuse authentication/session/role boundaries, PostgreSQL/Alembic, typed provider and
fake contracts, versioned orchestration, logging redaction, privacy operations and
seven-check CI. Planned knowledge entities are not implemented. Use an operator-only
quarantine/scan/sandbox/extract/chunk pipeline, a separate embedding port, immutable
spaces and approved corpus releases, exact filtered PostgreSQL/pgvector retrieval,
validated citations and fail-closed evidence handling. Keep provider/model switching.
See [RAG architecture](RAG_ARCHITECTURE.md) for schema, contracts, limits and lifecycle;
[RAG evaluation](RAG_EVALUATION.md) owns metrics, tests and reporting.

Mandatory: approved public sources, text PDF/UTF-8 validation, bounded sandboxed
extraction, provenance and source review, deterministic chunks, model/space isolation,
exact semantic retrieval, SQL authorization/currentness filters, immutable citations,
version activation/rollback, immediate revocation and approved purge, privacy-safe
audits, reproducible en/sw evaluation and operational runbooks.

Later enhancements: URL crawling/import, OCR, DOCX/HTML, ANN indexes, hybrid ranking,
reranking, automatic translation, staff-only corpora, upload/admin UI, streaming and
separate services. Do not add these to make the initial scope larger; consider only
with measured need and new approval. Mandatory retrieval safety is never optional.

## Proposed workstreams and tracking

No pre-existing P4 issues were found: only #39 and #44 were open before creation.
The seven workstreams below refine the existing Phase4 roadmap without redefining
its exit gate. All are planning issues assigned to Abdalla-Wasaa; issue creation is
not implementation approval. Each future PR targets main, uses focused Conventional
Commits, preserves seven checks and needs owner review/manual merge.

### [P4-01 — Public-document RAG contracts and architecture](https://github.com/Abdalla-Wasaa/Production-Grade-County-Government-AI-Assistant/issues/46)

Scope: Approve typed ingestion/retrieval/citation contracts, source/corpus state machines, role matrix and failure semantics before implementation. Define operator-only ingestion and authenticated bounded retrieval; no public upload or generation endpoint.

Dependencies: Merged planning PR; owner implementation approval.

Acceptance: Reviewed schemas and threat model; owner-selected source/file limits, embedding approach and resource budget; requirement-to-test matrix. No runtime grant implied.

Tests: Contract/schema rejection tests planned for unknown fields, oversized data, invalid identities and missing approval.

Deliverable/PR: Contract PR only; no migrations or runtime changes.

Security: quarantine/source approval, least-privilege operator/runtime separation,
redacted audits and exact changed-exposure approval are mandatory; no inherited
Phase3 runtime or security grant.

### [P4-02 — Sandboxed document ingestion and validation](https://github.com/Abdalla-Wasaa/Production-Grade-County-Government-AI-Assistant/issues/47)

Scope: Implement explicit operator ingestion with quarantine, file validation, scan-before-parse, bounded extraction/normalization/chunking and provenance. Synthetic fixtures only until source approval.

Dependencies: P4-01 reviewed contracts; parser/scanner dependency and runtime approvals.

Acceptance: All malicious/oversize/encrypted/active-content fixtures denied; repeated content idempotent; page/section provenance reproducible; no publication on partial failure.

Tests: Unit and isolated parser tests; malformed PDF, polyglot, decompression/resource bounds, secret/log redaction, duplicate/concurrent ingestion.

Deliverable/PR: Separate schema/operator ingestion PR; no live source fetching initially.

Security: quarantine/source approval, least-privilege operator/runtime separation,
redacted audits and exact changed-exposure approval are mandatory; no inherited
Phase3 runtime or security grant.

### [P4-03 — Embedding spaces and PostgreSQL vector storage](https://github.com/Abdalla-Wasaa/Production-Grade-County-Government-AI-Assistant/issues/48)

Scope: Implement separate typed embedding port and deterministic fake; reviewed pgvector-capable PostgreSQL packaging and migrations; immutable spaces/chunks/corpus membership.

Dependencies: P4-01 contracts; P4-02 chunk format; separately approved image/model/dependency decisions.

Acceptance: Fixed dimensions and finite vectors enforced; no mixed-space queries; unique chunk/space; empty DB upgrade and rollback/forward recovery documented; runtime cannot install extensions.

Tests: Real PostgreSQL migration, privilege, concurrent idempotency and dimension mismatch tests; fake embeddings in CI.

Deliverable/PR: Dedicated image/migration review before runtime; no embedding model download without approval.

Security: quarantine/source approval, least-privilege operator/runtime separation,
redacted audits and exact changed-exposure approval are mandatory; no inherited
Phase3 runtime or security grant.

### [P4-04 — Exact retrieval and source lifecycle filtering](https://github.com/Abdalla-Wasaa/Production-Grade-County-Government-AI-Assistant/issues/49)

Scope: Implement exact cosine retrieval over server-selected public approved current corpus and space, with mandatory SQL filters and deterministic tie-break; lifecycle revocation and rollback.

Dependencies: P4-02/03; approved retrieval contract.

Acceptance: Recall@5 >=0.85 per language on >=50 relevant held-out cases/language; zero unauthorized/withdrawn/expired hits; in-flight revocation fails closed; exact retrieval precedes ANN.

Tests: Bilingual gold-set retrieval, SQL injection, county/space/corpus isolation, concurrent withdrawal, cache invalidation and restored deletion replay.

Deliverable/PR: Retrieval-only PR with no model dispatch or browser generation.

Security: quarantine/source approval, least-privilege operator/runtime separation,
redacted audits and exact changed-exposure approval are mandatory; no inherited
Phase3 runtime or security grant.

### [P4-05 — Citation-aware grounded orchestration contracts](https://github.com/Abdalla-Wasaa/Production-Grade-County-Government-AI-Assistant/issues/50)

Scope: Prepare evidence envelope, strict citation validation and fail-closed orchestration using fakes. Preserve AIProvider; no unapproved generation endpoint.

Dependencies: P4-04 evidence contracts; #44 generation/context/usage contracts for integration; #39 gates before live integration.

Acceptance: Every emitted citation maps to selected eligible immutable version and exact page/span; missing/conflicting/expired evidence abstains; retrieved text cannot grant instructions/tools.

Tests: Mocked citation tampering, invented IDs/URLs, conflicting evidence, injection, truncation, deletion/revocation during generation and safe logging.

Deliverable/PR: Fake-only orchestration PR initially; live-generation integration remains blocked pending #39/#44 and exact approvals.

Security: quarantine/source approval, least-privilege operator/runtime separation,
redacted audits and exact changed-exposure approval are mandatory; no inherited
Phase3 runtime or security grant.

### [P4-06 — RAG evaluation and adversarial security evidence](https://github.com/Abdalla-Wasaa/Production-Grade-County-Government-AI-Assistant/issues/51)

Scope: Build reproducible synthetic bilingual retrieval/citation/adversarial sets, fixtures and reports; retain raw failures, corpus/space identities and hardware.

Dependencies: P4-02..05 testable artifacts; independent bilingual reviewer for semantic gates.

Acceptance: All RAG_EVALUATION.md gates reported per language with denominators; distinguish fake transport tests from real retrieval and human-reviewed generation; no threshold relaxation.

Tests: Offline unit, real-PG retrieval, parser isolation, source lifecycle, auth/cross-user, redaction and regression matrix; separately approved live evaluations only.

Deliverable/PR: Evaluation/security PR, preserve benchmark evidence and pending #39 status.

Security: quarantine/source approval, least-privilege operator/runtime separation,
redacted audits and exact changed-exposure approval are mandatory; no inherited
Phase3 runtime or security grant.

### [P4-07 — Public-document RAG acceptance and handover](https://github.com/Abdalla-Wasaa/Production-Grade-County-Government-AI-Assistant/issues/52)

Scope: Verify clean-checkout reproduction, corpus approval/release/rollback/purge, security, quality and operational instructions; record exact restricted acceptance scope.

Dependencies: P4-01..06 evidence; applicable owner approvals; #39/#44 for any live-generation acceptance.

Acceptance: Seven hosted checks green, fresh exposure/security decision for changed baseline, source-owner signoff, independent bilingual retrieval/semantic evidence where required, honest unresolved blockers; no production claim.

Tests: Clean checkout, migrations, lifecycle/recovery, load/resource reports, runbook replay and required CI.

Deliverable/PR: Separate acceptance documentation PR; owner manual merge; no automatic security renewal.

Security: quarantine/source approval, least-privilege operator/runtime separation,
redacted audits and exact changed-exposure approval are mandatory; no inherited
Phase3 runtime or security grant.

## Dependency and approval matrix

| Work | Independent fake/synthetic progress after future approval | Blocking decisions |
| --- | --- | --- |
| Contracts, fixtures and lifecycle design | Can proceed without live generation or #39 semantic results | Owner implementation/contract approval |
| Parser/chunker and source registry | Test synthetic files in isolated operator jobs | Parser/scanner selection, scans and exact runtime approval; no real documents yet |
| Vector schema and retrieval | Fake vectors test storage/filtering; separately approved embeddings needed for semantic recall | PostgreSQL extension image/package pin, dependency/license/model/space/dimension choice and exposure grant |
| Citation evidence wiring | Mocked provider verifies IDs, source eligibility, budgets and safe abstention | Reviewed evidence contract; no semantic/live-quality claim |
| Conversation generation integration | Remains blocked | #44 durable lifecycle/context/quota/UI contracts and #39 bilingual/latency gates; exact runtime authorization |
| Real document release or live evaluation | Not permitted by this plan | Source-owner approval, legal/privacy review where applicable, current security decision and separate ingestion/inference authorization |
| Full RAG acceptance | Retrieval-only evidence may be reported separately | No integrated/live acceptance while #39/#44 gates remain unmet |

P4-01 can start as contract/fixture source work only after explicit implementation
approval. Do not implement proposed endpoints or migrations before review. Decide:
file limits/parser/scanner, embedding model/license/runtime/dimension, immutable
PostgreSQL extension packaging, source approval operators, purge/backup/hold policy,
retrieval/resource thresholds and legal/privacy applicability. Changes to images,
dependencies and accepted exposure require separate assessment and decisions.

## Evidence, publication and next step

This PR changes planning documents and the roadmap only; no application, dependency,
image, model, security record or historical evidence change. Accepted exposure stays
015755bffa0f038986d719624979b317cb5e5527dceed76447fd207d09747ab1.
Renewal PR43 expiry stays30October2026 23:59EAT. Actual21October human CRITICAL
review is confirmed; future daily reviews remain due. Findings remain runtime115
HIGH/3CRITICAL plus builder56HIGH/1CRITICAL. Preserve invalidation conditions and
all seven app-bound checks/ruleset25222082. No automatic renewal or merge.

Run local repository/link, CI-policy, diff and secret checks and verify exposure
unchanged. Publish this documentation PR and require backend-quality,
postgresql-integration, python-dependency-audit, frontend-quality, compose-integration,
repository-quality and secret-scan to pass on its head. Reuse historical acceptance
evidence honestly; hosted CI is new evidence for this PR, not a model-quality review.
No local application tests, ingestion or inference are needed for planning documents.

Recommended first implementation task: P4-01 reviewable typed document/source,
embedding-space, retrieval/evidence and lifecycle contracts with deterministic
fixtures and a role matrix, before selecting parser/vector packages or migrating.
No P3-04, RAG integration, public services, real citizen/government documents or
production are authorized by this plan.

## WhatsApp-first planning reconciliation — 22 October 2026

The owner authorizes [ADR0006](DECISIONS/0006-whatsapp-first-framework-adapters.md)
and its [impact/workstream assessment](WHATSAPP_FIRST_IMPACT_ASSESSMENT.md) for
planning only. This supplements the approved workstreams above, not their runtime
permissions or acceptance gates. Existing issues46–52 are reused; no duplicate issues.

| Tracking | Proposed adapter-aware addition |
| --- | --- |
| #46 | Retain framework-neutral typed RAG contracts; preserve unexecuted prepared source branch pending exact testing grant; don't add SDKs or channel runtime to it |
| #47 | Review LlamaIndex as sandboxed ingestion transformations; application owns approval/version/revocation |
| #48 | Embedding port and pgvector remain canonical; no framework-default model/vector-store configuration |
| #49 | SQL-filtered RetrievalService remains authoritative; expose a bounded retriever mapping for LangChain |
| #50 | LangChain composition invokes AIProvider and typed evidence/tools, with one deadline/retry/budget policy |
| #51 | Add offline adapter/channel/injection/telemetry-isolation tests while retaining bilingual retrieval and independent semantic gates |
| #52 | Acceptance matrix distinguishes retrieval, channel transport, model quality and enabled live features; #39/#44 remain blockers |

Channel-neutral envelope/linking/inbox/outbox/usage and user-facing generation stay
under #44 contract review; independent quality and performance stay in #39. WhatsApp
and React operator implementation tasks need a later bounded breakdown/owner grant.
MCP is a proposal under Phase5's existing read-only tool gate; no Phase4 tool-runtime
scope creep. First proposed MCP fixture is a synthetic read-only service directory.

Implementation order: finish separately authorized #46 contracts; review #44 shared
channel identity/durable messaging contracts with synthetic fixtures; then separately
review minimal framework packages and #47/#48 source/vector work; add retrieval and
fake-only orchestration mappings before any live channel/tool/generation integration.
No framework installation, migration, source ingestion, embedding download, live
Meta/MCP/model request or public endpoint is authorized by this planning amendment.
