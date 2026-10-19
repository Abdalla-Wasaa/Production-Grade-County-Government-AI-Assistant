# Phase 3 implementation plan — approval pending

Phase 2 closed through owner-merged PR #29. Updated issue #30 now authorizes
P3-01 source implementation: provider contracts, fake and local Ollama/Llama adapter.
Runtime validation remains subject to its exact-exposure checkpoint. Subsequent
Phase 3 work in this plan still requires separate owner approval. Follow the existing
[roadmap](ROADMAP.md), [architecture](ARCHITECTURE.md),
[API specification](API_SPECIFICATION.md) and [security requirements](SECURITY.md).
No new milestone identifiers are assigned here; Phase 3 tracking/PR scope requires
owner approval. No live AI call, public rollout or production/citizen data is authorized.
The existing exception does not automatically cover Phase 3 exposure or survive
23 October 2026, 23:59 EAT.

## Small reviewable implementation sequence

| Order | Scope and dependency | Tests and completion evidence |
| --- | --- | --- |
| 1 | Define the backend provider interface: typed request/result/usage/error contracts and a deterministic fake. Reuse existing module/config/logging boundaries; no SDK/network dependency required. | Shared mocked contract tests cover English/Kiswahili requests, cancellation, normalized errors, usage and safe outputs. No live calls. |
| 2 | P3-01 now includes the local Ollama adapter with initial llama3.2:3b and mocked transport tests; see [AI providers](AI_PROVIDERS.md). Add an OpenAI adapter in a subsequent approved milestone. Verify a stable compatible SDK before adding/locking it. Model/provider choice stays server-configured and allowlisted; leave Azure OpenAI/Bedrock as future adapters. | Mock the SDK/transport for success, malformed results, timeout, rate limit, transient failure and authentication failure; run the same contracts against fake and adapter. No real key or live request in CI. |
| 3 | Add versioned prompt/response orchestration with reviewed synthetic service context, language choice, uncertainty/abstention and bounded conversation memory. Define exact model/output/context/deadline caps in the reviewed contract before code. | Prompt construction and isolation tests; exclude other users' history, expired/held-inaccessible content and secrets; enforce bounded input/output and safe plain-text responses. Do not treat model output as instructions. |
| 4 | Approve the separate generation API and durable attempt/retry schema before implementation. Reuse authenticated owned conversations and persisted user messages; preserve unanswered messages on failures. | Ownership/role/CSRF tests where applicable; idempotency, concurrent duplicate generation, cancellation/recovery, retention/deletion and no fabricated assistant messages. Do not overload the Phase 2 persistence-only endpoint. |
| 5 | Enforce per-user concurrency/rate/token/spend limits, overall deadlines, bounded retries and durable usage reservation/reconciliation. Reuse PostgreSQL transaction patterns and privacy-safe observability. | Exhausted quota, concurrent reservations, provider timeout/ambiguous completion and recovery tests; bounded Retry-After handling, no unbounded retry or double charge/write. Verify configured limits and sanitized metrics. |
| 6 | Integrate bilingual generation UI only after reviewed backend contracts. Keep session/auth/history behavior and accessibility conventions. | Mocked frontend/browser tests for loading, timeout, unavailable provider, abstention, retry and persisted responses; preserve all seven CI checks and owner PR review. |

## Keys, privacy and operational gates

OpenAI credentials are backend-only private configuration, with validation/redaction;
never source control, frontend/VITE configuration, browser storage, reports or logs.
Use synthetic fake credentials in tests. AWS secret-manager/deployment integration
is a later approved infrastructure decision. Do not send conversation contents to a
provider until the required provider/data-retention/privacy approval is explicit.
No raw prompt/message/credential logging, implicit public registration, tools, RAG,
payments or agents are added by this plan.

Provider timeouts/cancellation must release resources; retries need explicit bounded
semantics and durable attempt identity so ambiguous outcomes do not silently repeat
costly operations. Add explicit migrations only after schema/contract approval.
Fresh dependency/container scans and focused exposure review precede execution under
any changed-exposure exception; the old development decision is not inherited.

The existing Phase 3 roadmap also requires reviewed synthetic catalogue/evaluation
content, held-out bilingual cases, per-language gates and load/budget evidence. Those
remain Phase 3 exit criteria, not claims satisfied by mocked adapter tests.

**First implementation task after approval:** add the typed provider interface and
deterministic fake with shared contract tests. The updated P3-01 scope also includes the Ollama adapter with mocked tests.
An OpenAI adapter remains future work; live-provider execution requires a separate
explicit gate.
