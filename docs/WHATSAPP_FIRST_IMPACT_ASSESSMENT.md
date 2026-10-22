# WhatsApp-first architecture impact and incremental migration

Planning date:22 October2026. [ADR0006](DECISIONS/0006-whatsapp-first-framework-adapters.md)
records owner direction; this is not implementation/runtime approval.

## Verified baseline and preserved work

PR53 is merged at4f534cd637bf2fec742aa3b1cbf5795a19ac4738; main was synchronized
fast-forward from a clean tree. All seven checks on that PR passed. Issues46–52,
39 and44 remain OPEN. No duplicate tracking issue is necessary.
P4-01 prepared source is preserved on feat/p4-01-rag-contracts at
fc9e0a6d807f977a6cbb8da77460b490440fc431 (104 tests prepared, not run/pushed).
Its new exposure9181213fb3009076b66739cb99d89a6c1eefb5f0ad3a1759c0868252c077daf4
is not accepted. This documentation branch starts from merged main, does not include,
cherry-pick, execute or overwrite that source, and does not approve it retrospectively.
P4-01 framework-neutral contracts remain a useful candidate; review for channel-neutral
compatibility before executing them under their separate exact-source grant.

Main's recorded exact exposure remains
015755bffa0f038986d719624979b317cb5e5527dceed76447fd207d09747ab1.
Security expiry is30October2026 23:59EAT. Actual21October review is historical;
22October human CRITICAL review is unconfirmed. Do not infer it from this amendment.
Runtime115HIGH/3CRITICAL and builder56HIGH/1CRITICAL remain recorded; this review
performs no new scans or security acceptance. Daily reviews/invalidation remain.

## Impact classification

| Area | Classification | Compatibility and acceptance requirement |
| --- | --- | --- |
| Backend runtime and explicit migrations | Reuse unchanged | One domain backend; explicit schema upgrades, no startup DDL |
| JWT/cookies/CSRF, web ownership/history/privacy | Reuse unchanged | Existing routes/clients and deny/cascade/hold regressions stay green |
| AIProvider/fake/Ollama configuration | Reuse unchanged | Framework invokes through port; no model/client substitution |
| React citizen UI | Extend through adapters | Remains supported alternative; share domain workflow, accessible en/sw behavior |
| React operator/admin UI | New component | Separate privileged contracts/authentication; no general citizen-history browser |
| Channel identity/linking | New component | Explicit verified links, no phone/email auto-merge or public onboarding implied |
| Messages/attempts/delivery | Refactor with compatibility requirements | Add channel-neutral envelope/inbox/outbox; Phase2 user-message persistence semantics stay intact |
| Prompt orchestration | Extend through adapters | LangChain mapping retains versioned system/data separation, budgets, normalized errors |
| Ingestion/extraction/index build | Extend planned adapters | LlamaIndex behind sandbox; application owns immutable sources/chunks and activation |
| Exact retrieval/citations | Reuse planned boundary | Server-owned filters/release/space, validation and immediate revocation unchanged |
| DB schema | New additive entities | Channels/links/events/deliveries/consent; separate reviewed migrations, no changes now |
| MCP tools | Extend planned Phase5 tool boundary | Registry, per-tool authorization/read-only policy; no Phase4 live-tool expansion |
| Deployment/public webhook | New exposure | TLS/edge/WAF/secrets/incident/privacy approvals; loopback development remains |
| CI/CD | Extend offline tests later | Meta/framework/MCP mocks, no external services or real messages in CI |
| Monitoring/performance/cost | Extend through adapters | Content-free queue/provider/delivery timings and quotas; no unapproved telemetry export |
| Existing components | None deprecated | No rewrite or removal justified by this planning decision |

## Proposed workstream reconciliation and tests

| Order / existing tracking | Minimal proposed delta | Acceptance and deterministic test strategy | Separate approvals |
| --- | --- | --- | --- |
| 1: #46 P4-01 | Keep typed RAG contracts independent of frameworks/channels; document adapter mapping | Existing source IDs/filter/lifecycle tests; no SDK types; verify current prepared candidate separately | Exact source testing and later security/publication decision |
| 2: #44 deferred MVP | Review channel-neutral envelope, identity/link, inbox/outbox, attempts and quota contracts before channels | Duplicate/reordered events, takeover/linking, account disable, holds/deletion, restart and ambiguous sends; all existing APIs compatible | Contract/schema/identity policy, privileges, exact runtime; no implementation grant now |
| 3: #47 ingestion | Select minimal LlamaIndex transformations behind parser sandbox; source owner remains authority | Malformed/active files, metadata fidelity, stable chunk IDs, no network or implicit LLM/embedding, revocation/purge | Packages/licenses/scans and parser environment; no actual files ingested now |
| 4: #48 vector storage | Framework-neutral EmbeddingProvider and pgvector repository remain authoritative | Fixed dimensions/space, unique identities, fake embeddings and approved PG migration/privilege tests | Model/package/database-image choices and execution |
| 5: #49 retrieval | Application exact retrieval; small LangChain mapping only if needed | SQL currentness/scope/release filters; revoked source never returned; Recall@5 unchanged | Dependency review if shim imports LangChain |
| 6: #50 orchestration | Bounded LangChain composition through existing model/retrieval ports | Same fake/provider contracts, no duplicate retries/memory/client; citation validation, timeout/cancel/log tests | Framework pin/inventory and exposure grant; #39/#44 before live integration |
| 7: #51 evaluation | Add mocked channel/framework and indirect-injection suites | en/sw per-channel content quality, delivery outcomes distinct from model passes, redaction, cold/warm and queue timing | Human bilingual review and separately approved performance/live workloads |
| 8: #52 acceptance | Include source/channel/operator runbooks and exact enabled-feature matrix | Clean checkout, seven CI checks, replay/recovery/withdrawal/purge and current security review | Explicit owner acceptance; no production claim |
| Later Phase5, existing tool roadmap | Synthetic read-only MCP directory tool proposal | Unknown server/tool/schema/scope rejected; timeout/cancel/audit and no external connectivity | New scoped tool contracts, endpoint/credential/runtime review; no MCP runtime now |

WhatsApp adapter contracts and React operator work should first be scoped under #44;
create an implementation breakdown only after owner review, rather than duplicating
RAG issues or assigning invented milestone numbers. No code branch is authorized by
these proposed tasks. Source approval, documents and retrieval can be independently
tested with fixtures; live conversation generation remains blocked by #39/#44.

## Operational and cost implications

A webhook adds an internet ingress and vendor dependency; it is not covered by local
Compose approval. Bound ingress requests, per-sender/business/county rates, durable
queue depth, worker concurrency, retry budgets and outgoing spend. Separate webhook
acknowledgment from model completion; no model waits under DB locks. Include queue,
parse, retrieval, provider and delivery stages in end-to-end latency. Neither model's
existing p95/timeout failures nor independent bilingual assessments are resolved.

Record costs by transport/template category, country, vendor, embedding/model usage,
DB/storage/scanner and infrastructure. Obtain current official pricing and owner caps
before a trial; invent no fixed rate or measured improvement. Framework composition
may increase dependencies, allocations, serialization and retries; benchmark against
the existing direct-provider baseline. No higher deadline to conceal overhead.

## Open owner decisions before implementation

Approve onboarding/account-link policy, canonical owner semantics and operator
privileges; choose exact Meta API version and authorized county/business identity;
confirm platform use eligibility, messaging templates/consent, privacy/data locations,
retention/erasure/holds and human escalation owner. Obtain current business-platform
terms through an authorized reviewer: terms page access redirected to login during
this review; no eligibility approval can be inferred. Government identity/branding
and any AI-use restrictions must be reviewed explicitly before account activation.

Select minimal LangChain/LlamaIndex/MCP versions/modules only after locked resolution,
Python/Pydantic/async compatibility, vulnerability/license and no-telemetry/default
model-call review. Decide queue lease/reconciliation, edge and secrets design before
public endpoint implementation. Review proposed schemas/API separately. Preserve
existing exact-source approvals and security expiry; do not begin live connections,
RAG, inference, real-data processing or production from this document.

Recommended first task: review #46's existing framework-neutral candidate and its
exact testing checkpoint, then review #44 channel-envelope/linking contracts with
fake events. Do not add frameworks or WhatsApp runtime to P4-01.
