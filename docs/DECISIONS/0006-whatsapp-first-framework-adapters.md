# ADR 0006: WhatsApp-first channels and bounded framework adapters

Date: 22 October 2026. Status: owner-approved target direction for planning;
documentation PR review pending. Implementation and runtime approvals are separate.

## Context

The existing modular monolith implements web authentication/history and provider/
prompt foundations; RAG remains planned. The owner now directs WhatsApp as primary
citizen channel, React as alternative citizen channel and future operator/admin UI,
LangChain for orchestration, LlamaIndex for document intelligence and MCP for approved
tools. None of those channel/framework integrations currently exists.

## Decision

Retain FastAPI, PostgreSQL/pgvector direction, domain services, AIProvider, ownership,
privacy and RAG approval/revocation. Introduce anti-corruption adapters, not framework
objects in domain/API/database contracts. The application owns identities, messages,
source lifecycle, retrieval authorization, budgets, attempts and audit records.

- WhatsApp adapter verifies Meta events and maps them to a channel-neutral inbox.
  Web retains existing JWT/cookie/CSRF contracts and persistence-only semantics.
- A durable inbox/outbox and bounded worker process from the same backend artifact
  support future asynchronous transport. This extends the target synchronous-HTTP
  turn design for channels; it does not replace existing Phase2 endpoint behavior.
  PostgreSQL is the proposed durable queue; broker adoption needs measured need.
- LangChain composes prompts, retrieval and bounded invocation/tool flows through
  application ports. AIProvider remains the only approved model boundary; there is
  no alternate framework model client, automatic agent loop or framework-owned memory.
- LlamaIndex is an ingestion transformation/index-build adapter within the approved
  sandbox. It emits application-owned chunks/provenance; no competing source registry,
  live vector store, retrieval engine or automatic document deletion authority.
- Application RetrievalService owns SQL-filtered exact pgvector queries. A LangChain
  retriever shim maps typed evidence; neither framework bypasses source eligibility.
- MCP is a transport behind a deny-by-default tool service/registry. Tool discovery
  is not approval; read-only defaults and server-side authorization remain mandatory.

React admin/operator screens are proposed workflow clients, not permission to expose
existing host-operator credentials/CLIs over HTTP. New server-side privileged APIs,
strong operator authentication/MFA and least-privilege grants need separate contracts.
No citizen JWT admin role gains unrestricted histories, source publication or tools.

## Compatibility, consequences and alternatives

Preserve existing auth and conversation APIs, raw provider/error contracts and
immutable source identities. Channel/link/delivery state needs reviewed additive
migrations and deletion/hold/recovery tests. Existing consumers do not receive
framework objects or mandatory WhatsApp identities. Do not auto-link accounts by
phone/email or authorize public registration through this decision.

Selected framework packages/versions, Python3.12/Pydanticv2/async compatibility,
licenses, transitive inventory, model I/O mapping, hidden retries and telemetry need
review before installation. Pin only necessary modules. Trace/callback instrumentation
must exclude content/credentials and remain local by default. Benchmark framework
overhead separately; the existing 15-second target and30-second hard deadline stand.
Do not add LangGraph, a broker, remote tracing, cloud parsing or a new model by default.

Rejected alternatives: rewrite domain services into framework chains; make LlamaIndex
and LangChain competing retrieval owners; new microservices by channel; model-decided
access or identity links; WhatsApp history merged into web without explicit linking.

## Authorization and preserved gates

Owner attachment “ARCHITECTURE AMENDMENT — WHATSAPP-FIRST COUNTY GOVERNMENT AI
ASSISTANT” explicitly authorizes analysis, documentation, one PR and seven normal
checks only. The unchanged baseline exposure is
015755bffa0f038986d719624979b317cb5e5527dceed76447fd207d09747ab1; expiry stays
30 October 2026, 23:59 EAT. No security-record edits or future-runtime grant.
#39/#44 remain open. No live WhatsApp/webhook, public network/tunnel, inference,
embedding download, ingestion, real data, production or automatic merge is authorized.

See [impact assessment](../WHATSAPP_FIRST_IMPACT_ASSESSMENT.md),
[channel design](../ARCHITECTURE.md#whatsapp-first-target-amendment--22-october-2026),
[API proposals](../API_SPECIFICATION.md#proposed-channel-contracts--not-implemented)
and [threat delta](../SECURITY.md#whatsapp-and-framework-threat-delta--planning-only).
