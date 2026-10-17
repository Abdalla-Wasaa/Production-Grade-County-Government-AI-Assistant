# ADR 0001: Modular monolith with application-managed AI state

Date: 2026-10-13. Status: proposed implementation baseline for user review.
Documentation is complete; implementation and merging still require approval.

## Context

The County Government AI Assistant needs bilingual information assistance,
private conversation history, controlled AI integration, and later secure retrieval
and tools. A small development team needs testable boundaries without operating
multiple distributed services. [Coursework findings](../COURSEWORK_REVIEW.md)
support separating API contracts, configuration, retrieval, policy and evaluations,
while exposing gaps in durability, authorization and deployment evidence.

## Decision

Use React/Vite/Tailwind CSS for the frontend; one Python/FastAPI/Pydantic backend
with identity, conversations, AI, knowledge and tools modules; SQLAlchemy and
PostgreSQL for persistence. Expose module service interfaces and keep SDK/SQL
details behind adapters/repositories. Use Alembic migrations when implementation
begins. The static frontend and backend are separate build artifacts; the backend
remains one application, not a network of microservices.

Start with an OpenAI adapter behind a vendor-neutral provider port. Keep conversation
state and bounded context in PostgreSQL/application logic, not vendor threads.
Introduce pgvector only in the RAG milestone. Use Docker/Compose locally and
GitHub Actions for gates; make AWS deployment a later, explicit decision.

## Decisions and tradeoffs

| Decision | Benefit | Cost / mitigation |
| --- | --- | --- |
| Modular monolith over microservices | Simpler transactions, deployment and local testing | Shared failure/scaling boundary; enforce module imports and measure bottlenecks |
| PostgreSQL + SQLAlchemy over demo SQLite | Durable relational constraints and multi-worker concurrency | Requires managed connections, migrations, backups and genuine PostgreSQL tests |
| Application-managed history | Ownership, deletion and vendor portability remain explicit | Must implement token budgeting, ordering and retry recovery |
| OpenAI first, adapters later | Small initial integration with an expansion boundary | Adapter contract cannot erase vendor capability/privacy differences; test each adapter |
| Small approved catalogue before document RAG | Scope and evidence can be reviewed quickly | Limited coverage; abstain rather than answer undocumented county questions |
| Synchronous nonstreaming turn response | Easier first API/UX contract and safety validation | Latency and crash recovery; persist attempt state and expose pending/retry outcomes |
| Invite-only authentication pilot | Avoids rushed public identity/onboarding workflows | Limited participation; public launch needs recovery, verification and staff federation/MFA |
| pgvector later over separate vector service | Potential shared relational authorization/provenance | Vector workloads contend with OLTP; benchmark filters/indexes before activation |
| Read-only tools before consequential actions | Testable permissions with fewer operational hazards | Transactions require separate confirmation and officer workflows later |

Alternatives deferred: microservices, Kubernetes, a dedicated vector database,
provider-managed conversation storage, a general agent framework, and fine-tuning.
They add operational or data-lifecycle complexity without current measured need.
No coursework projects or private datasets are imported into the new application.

## Consequences and review triggers

Require cross-user tests, transaction boundaries, provider fakes, bilingual held-out
evaluation, and reviewed privacy/hosting choices. Extract a module into a service
only when measured load, isolation, team ownership or availability needs justify
the distributed cost. Revisit synchronous turns if deadlines or interactive UX
require durable queues/streaming. Revisit identity before public onboarding and
tenancy before serving multiple counties.

Related: [architecture](../ARCHITECTURE.md), [requirements](../REQUIREMENTS.md),
[database](../DATABASE_DESIGN.md), [API](../API_SPECIFICATION.md),
[security](../SECURITY.md), [roadmap](../ROADMAP.md).

## Implementation record, 17 October 2026

The proposed-status header records the original Phase 0 decision context. Phase 0
merged in PR #1; P1-01 through P1-05 implement its foundation through PR #14. P1-06
checks that evidence without replacing this architectural decision. Domain modules,
provider calls, RAG/tools and production deployment remain future approved phases.
No additional ADR or changed architecture is introduced by documentation acceptance.
