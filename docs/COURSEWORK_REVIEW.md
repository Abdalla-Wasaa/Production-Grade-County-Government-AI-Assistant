# AI Engineering coursework review

Reviewed on 2026-10-13 for the County Government AI Assistant.

## Scope and method

The reference root is `/root/AIEngineeringClass/afyaplus-ai-week1`.
This is a static, read-only review of authored Python, documentation, tests,
configuration, Docker files, and CI workflows. No coursework modules were
imported, scripts executed, dependencies installed, models invoked, or datasets
copied. Source links below resolve against the local coursework root; they will
not resolve on GitHub unless that separate coursework tree is available.

Inspected examples cover `venv/wk1` through `venv/wk10`, the week 1, 2, 3, 4,
5 and 6 capstones, the top-level week 8, 9 and 10 capstones, and
`module4-capstone`. The review samples relevant implementations rather than
claiming a line-by-line audit of every project. Installed packages, model weights,
private data, environment files, and generated notebook outputs are not design
evidence. No authored `.ipynb` files were found in the coursework scan excluding
dependency and environment internals; no notebook implementation is claimed.

Code presence proves an implementation exists, not that it runs successfully or
has been deployed. Test and CI definitions were inspected, not executed. Existing
README statements about training or deployment are not independently verified
runtime evidence. Recommendations below are design proposals, not new features
or approved technology selections.

## 1. Existing practices worth reusing

### Modular Python and explicit configuration

- [Week 2 settings](../../venv/wk2_capstone_project/src/afyaplus_agent/config.py)
  defines a frozen `Settings` dataclass, a cached settings loader, project-relative
  paths, and a missing-cloud-credential check. Apply centralized configuration to
  county document locations, provider endpoints, model IDs, and retrieval limits.
  Validate values and secret handling before adapting this pattern.
- [Week 2 orchestrator](../../venv/wk2_capstone_project/src/afyaplus_agent/agent/orchestrator.py)
  separates model construction, retrieval tools, and agent construction;
  [session management](../../venv/wk2_capstone_project/src/afyaplus_agent/memory/session.py)
  separates conversation identity from orchestration. Use corresponding boundaries
  for API contracts, application services, retrieval, provider adapters, and
  authorized county tools. Reuse the separation, not clinical logic.
- [Week 8 pytest/Ruff configuration](../../Week_8_Capstone_Project/pyproject.toml)
  explicitly selects test locations and lint rules. Define a coherent package and
  tool configuration for the new project rather than relying on terminal location.

### FastAPI, Pydantic, and authorization

- [Week 6 HTTP entry point](../../venv/wk6_capstone_project/service/main.py)
  uses a separate agent router, dependency-based role checks, explicit response
  models, a public health route, and request tracing. Apply these patterns to
  versioned county-service routes with thin handlers and testable services.
- [Week 6 contracts](../../venv/wk6_capstone_project/service/models.py)
  demonstrate `Field` length/range/pattern constraints and `Literal` response
  categories. Validate citizen questions, department identifiers, pagination,
  citation objects, and tool arguments at boundaries; validate model output too.
- [Week 6 authentication](../../venv/wk6_capstone_project/service/auth.py)
  verifies bcrypt hashes, signs expiring JWTs, and distinguishes 401 from 403.
  [Week 9 API](../../Week_9_capstone_project/app.py) additionally requires JWT
  claims and checks issuer/audience. [Role matrix](../../Week_9_capstone_project/rbac.py)
  defaults unknown roles to no permissions. Adapt the authorization patterns for
  citizen, staff, and administrator capabilities; demo accounts are not reusable.
- [Week 9 RBAC tests](../../Week_9_capstone_project/tests/test_rbac.py)
  check expired tokens, denied roles, resource scope, and minimal tool listings.
  Use equivalent tests to prevent cross-county or cross-department access.

### Prompt engineering and LLM integrations

- [Week 1 few-shot classification](../../venv/wk1/thur/few_shot_urgency.py)
  separates the system task, user/assistant examples, and live user message.
  Adapt this to department routing with approved examples and an unknown-intent
  outcome; evaluate English and Kiswahili separately.
- [Week 1 structured extraction](../../venv/wk1/thur/lab13_structured.py)
  requests JSON-object output and parses it. This is a useful starting point for
  structured service requests, but `json.loads` alone does not validate the schema.
- [Week 1 capstone](../../venv/wk1_capstone_project/app.py) contains asynchronous
  HTTP provider calls, explicit timeouts, exponential waits for connection/timeouts,
  usage/latency extraction, and an Ollama fallback. Apply bounded provider adapters
  with observable failures; do not silently change data destinations or guarantees.
- [Week 2 orchestrator](../../venv/wk2_capstone_project/src/afyaplus_agent/agent/orchestrator.py)
  implements a `ChatOllama` agent with instructions to retrieve policy sources and
  report unavailable evidence. Apply source-first county policy answers. Prompt
  instructions remain advisory; code must enforce tool permissions and limits.
- [Week 8 prompt pin validation](../../Week_8_Capstone_Project/check_prompt_pin.py)
  checks semantic version, filename, content version, SHA-256, and configuration
  agreement. Version and hash approved county prompts, recording them with model
  and corpus versions in evaluation artifacts.

### Retrieval and embeddings: verified implementations

- [Week 2 ingestion](../../venv/wk2_capstone_project/src/afyaplus_agent/rag/ingest.py)
  actually constructs Hugging Face embeddings, semantic chunks, a persistent Chroma
  collection, and a LlamaIndex vector index. It rejects missing input documents.
  Adapt the ingestion stages for approved public county documents after provenance
  and access checks; library presence is not evidence of retrieval accuracy.
- [Week 2 retrieval](../../venv/wk2_capstone_project/src/afyaplus_agent/rag/retriever.py)
  loads the index, applies top-k and a similarity cutoff, synthesizes through Ollama,
  lists source filenames, and reports when no source survives. Reuse retrieval,
  abstention, and citation boundaries; calibrate thresholds on county queries.
  The docstring's claim that the tool never fabricates is stronger than the code
  guarantees: source nodes do not prove every generated claim is supported.
- [Module 4 retrieval](../../module4-capstone/services/triage/rag.py) is a separate
  deterministic token-overlap lookup with record IDs and file citations. It does
  not compute embeddings or call an LLM. Keep such an offline baseline for county
  directory lookups and regression tests alongside any future semantic retriever.
- [Week 10 search](../../Week_10_Capstone_Project/analytics/search.py) uses
  bag-of-words cosine scores, filters zero results, and breaks ties by SKU.
  [Its README](../../Week_10_Capstone_Project/README.md) explicitly states manual
  image tags, synthetic fixtures, and no CLIP inference. Reuse deterministic
  ranking and honest provenance, not claims of pretrained multimodal retrieval.
- [Week 10 encoder checker](../../venv/wk10/tuesday/check_encoder_pin.py) rejects
  floating revisions and requires fallback disclosure. Pin embedding revisions
  and disclose whether an evaluation used the production encoder or a proxy.
- [Week 9 corpus checker](../../venv/wk9/monday/check_corpus_pin.py) compares
  knowledge files against committed SHA-256 values and fails on missing or changed
  files. Adapt corpus integrity checks for county releases; a matching hash proves
  identity, not source authority, freshness, or approval.

### AI evaluations and data provenance

- [Week 3 lexical evaluator](../../venv/wk3/monday/evaluator.py) implements BLEU,
  ROUGE, and token F1. [LLM judge](../../venv/wk3/monday/llm_judge.py) defines
  correctness, groundedness, relevance, and helpfulness dimensions. Use multiple
  signals for county answers; text overlap is not factual correctness and a judge
  needs schema validation and human calibration.
- [Week 3 shared schemas](../../venv/wk3_capstone_project/shared/schemas.py)
  models evaluation, drift, and cost records. Use stable validated result schemas
  to compare prompts and models and report latency/cost with quality.
- [Week 4 data preparation](../../venv/wk4_capstone_project/data_prep.py) rejects
  duplicates, validates cited guidance, seeds splits, and keeps scenario paraphrases
  in the same split. Apply group-disjoint splits to county FAQ/service scenarios
  so nearly identical questions cannot inflate held-out performance.
- [Week 4 provenance](../../venv/wk4_capstone_project/provenance.py) checks source
  hashes, clause/page anchors, review hashes, and named/dated human decisions.
  [Tests](../../venv/wk4_capstone_project/tests/test_provenance.py) distinguish
  structural validity from human approval and reject changed evidence. Adapt this
  to county document ownership and departmental review without copying records.
- [Week 4 training entry point](../../venv/wk4_capstone_project/fine_tune.py)
  gates training on provenance, requires CUDA, resolves model revision, checks token
  lengths, and records run metadata. Reuse reproducibility principles if later
  evidence justifies fine-tuning; this review does not recommend training now.
- [Week 8 evaluation gate](../../Week_8_Capstone_Project/eval_prompts.py) rejects
  empty/duplicate sets, missing outputs, invalid labels, and unreviewed quarantine;
  it exits unsuccessfully below threshold and identifies stub versus recorded
  results. Apply explicit gates with a reviewed county benchmark and fixed
  denominator, rather than importing its teaching threshold.

### Database, caching, privacy, and observability

- [Week 7 batch worker](../../venv/wk7/thursday/batch_worker.py) uses SQLite,
  parameterized statements, and persisted job status. [Retry extension](../../venv/wk7/thursday/batch_retry.py)
  increments attempts before work and retires exhausted jobs. Reuse parameterization
  and bounded retry/dead-letter concepts for document ingestion, with proper
  transactions and concurrency controls.
- [Week 7 cache](../../venv/wk7/thursday/cache_triage.py) implements Redis TTL,
  an in-memory fallback, and hit/miss counters around a stub response. Cache
  approved public FAQ results with corpus/model/prompt versions in keys and strict
  user-scope rules; do not share private citizen answers by message alone.
- [Week 9 audit helper](../../Week_9_capstone_project/redact_then_hash.py) redacts
  sensitive patterns before hashing and uses restricted action/outcome fields.
  [Retention sweep](../../Week_9_capstone_project/retention_sweep.py) records
  requested/completed deletion and replaces a file through a temporary path.
  Reuse minimization and auditable lifecycle concepts, not the demo identifiers,
  policy durations, or an assumption that hashing is anonymization.
- [Week 3 instrumented API](../../venv/wk3/tuesday/instrumented_llm_app.py)
  exposes Prometheus request/latency metrics; [drift monitor](../../venv/wk3/tuesday/drift_monitor.py)
  checks distributions of input length, ROUGE, latency, and tokens. Track county
  quality, retrieval misses, failures, costs, and language coverage without logging
  raw citizen messages. Drift should trigger investigation, not automatic retraining.

### Docker, deployment, Git, and tests

- [Week 8 Dockerfile](../../Week_8_Capstone_Project/Dockerfile) installs a lockfile,
  validates prompt pins, runs as a non-root user, and defines a health check.
  [Docker ignore rules](../../Week_8_Capstone_Project/.dockerignore) exclude local
  secrets and artifacts. Adapt these patterns to a minimal county API image.
- [Week 3 Compose](../../venv/wk3/tuesday/docker-compose.yml) wires API health,
  Prometheus, Grafana, read-only configuration mounts, and persistent volumes.
  Reuse local observability topology after removing insecure demo defaults.
- [Week 8 pipeline](../../Week_8_Capstone_Project/scripts/pipeline.py) stops on
  failed subprocesses before build/deployment. [CI workflow](../../Week_8_Capstone_Project/.github/workflows/ci.yml)
  orders lint, tests, evaluation, tool health, build, and a main-only stub deploy.
  Adapt quality gates and artifact identity; deployment here is explicitly a stub.
- [Week 6 contributing guide](../../venv/wk6_capstone_project/docs/CONTRIBUTING.md)
  documents issue acceptance criteria, short-lived branches, Conventional Commits,
  PR review, and truthful conflict evidence. [Module 4 PR template](../../module4-capstone/docs/PR_TEMPLATE.md)
  requires actual test/evaluation evidence and distinguishes blockers from nits.
  Apply review discipline under this repository's `AGENTS.md`; do not import
  coursework-specific exclusions or interpret documentation as enforced protection.
- [Module 4 retrieval tests](../../module4-capstone/tests/unit/test_rag.py) verify
  provenance, empty queries, and no matches with temporary fixtures.
  [Week 6 service tests](../../venv/wk6_capstone_project/tests/test_service.py)
  cover 401/403/422, health, and tracing. Reuse behavior-focused unit, contract,
  authorization, and opt-in integration tests with synthetic county fixtures.
- [Module 4 architecture](../../module4-capstone/docs/architecture.md) and
  [deployment guide](../../module4-capstone/docs/deployment.md) explicitly disclose
  deterministic behavior and unexecuted cloud deployment. Preserve this distinction
  between planned capability, implementation, and measured evidence.

## 2. Practices requiring improvement for production

| Verified source | Limitation | Required adaptation |
| --- | --- | --- |
| `module4-capstone/services/triage/app.py` | API-key check is skipped when unset; live handler raises `NotImplementedError`; request text is unconstrained and response is an untyped dictionary. | Fail closed for protected routes, define public versus staff access, bound inputs, validate outputs, and make unavailable providers explicit. |
| `module4-capstone/agents/router.py` | Loads configuration from the process working directory at import and routes unknown text to the first tool. | Validate settings during startup, resolve package paths, and use an explicit unknown/escalation result. |
| `venv/wk1_capstone_project/app.py` | Interpolates untrusted user text into the system message; safety is substring matching; JSON schema is descriptive rather than enforced; fallback catches broadly. | Separate trusted instructions from user data, validate generated objects, classify failures, and bound retries under one deadline. |
| `venv/wk3/tuesday/instrumented_llm_app.py` | Calls synchronous `invoke` inside an async route; metrics count only successful calls and latency uses wall-clock time. | Use asynchronous provider calls or controlled workers, pooled clients, monotonic timing, and failure/cancellation metrics. |
| `venv/wk2_capstone_project/src/afyaplus_agent/rag/ingest.py` and `rag/retriever.py` | Deletes the current collection on rebuild; may ingest automatically during retrieval initialization; citations are filenames; errors can include raw exception text. | Separate ingestion jobs, version indexes and switch atomically, retain rollback, expose stable public citations, and sanitize errors. |
| `venv/wk2_capstone_project/src/afyaplus_agent/memory/session.py` | In-memory history and a plaintext PII map have no durable multi-worker lifecycle or expiry. | Scope sessions to authenticated owners; define retention, encryption, deletion, and persistent storage only where needed. |
| `venv/wk2_capstone_project/src/afyaplus_agent/config.py` | Cloud detection uses substring matching and secret fields are ordinary dataclass strings. | Validate endpoint host/scheme, avoid secret-bearing representations, and validate numeric ranges and allowed providers. |
| `venv/wk6_capstone_project/service/auth.py` | Embedded demo accounts; lacks the issuer/audience requirements present in the Week 9 example. | Use managed identity and verified claims, rotation/revocation, and server-enforced resource authorization. |
| `Week_9_capstone_project/injection_guard.py` | Unicode-normalized regex blocks a small set of override phrases. | Add adversarial evaluation and tool/data isolation; keyword checks cannot establish prompt-injection safety. |
| `venv/wk7/thursday/batch_worker.py` and `batch_retry.py` | Workers select pending jobs without atomic claims; one poison row can fail a whole batch. | Add atomic leases, per-job retries, idempotency, crash recovery, migration tracking, and connection cleanup. |
| `venv/wk7/thursday/cache_triage.py` | Key contains only normalized text; silently falls back to process memory; probes Redis during import. | Include access scope and artifact versions, disclose degraded state, bound memory, and initialize dependencies through lifecycle management. |
| `venv/wk3/monday/llm_judge.py` and `evaluator.py` | Judge JSON has no score-range schema; parse failures become zero scores; evaluator downloads resources during import. | Distinguish evaluator failure from bad answers, validate scores, pin judge artifacts, calibrate with reviewers, and prepare resources explicitly. |
| `module4-capstone/evals/run_eval.py` | Evaluates routing only and returns success regardless of score; documented golden set has three cases. | Add enforceable quality thresholds and representative service, language, citation, refusal, and permission cases. |
| `Week_9_capstone_project/redact_then_hash.py` and `retention_sweep.py` | Hashing can collapse redacted identifiers; flat-file audit/deletion lacks a durable transactional or tamper-resistant boundary. | Use scoped identifiers, explicit retention decisions, protected audit storage, and recoverable deletion workflows. |
| `venv/wk3/tuesday/docker-compose.yml` | Contains demo Grafana credential defaults and host-published monitoring ports. | Supply managed credentials and restrict monitoring access; never carry demo defaults into production. |
| `Week_8_Capstone_Project/Dockerfile` and CI workflow | Base image tag and action major-version tags are mutable; a stub deployment is not operational deployment proof. | Evaluate digest/SHA pins, dependency and image scanning, signed provenance, real readiness checks, and tested rollback. |
| `module4-capstone/tests/test_security_smoke.py` | Secret check targets one key pattern in Python and skips tests/venv paths. | Scan relevant tracked files and history with a dedicated scanner; ignore rules alone cannot prevent leaks. |
| `module4-capstone/requirements.txt`, `Week_8_Capstone_Project/requirements.lock`, and `venv/wk2_capstone_project/requirements.txt` | Dependency discipline varies: Module 4 is unpinned, while other projects pin versions; inspected lock entries have no package hashes. Compatibility was not executed. | Resolve an independent minimal dependency set, record reproducible locks/hashes, and verify compatibility and vulnerabilities in the approved implementation phase. |

These are static findings, not a security certification. Existing coursework
history, credentials, datasets, and public release claims were not audited or copied.

## 3. New concepts to introduce for the county assistant

These capabilities were not verified as complete implementations in the reviewed
samples. Some coursework contains partial building blocks, as identified above.

1. **County knowledge governance.** Introduce an approved source registry with
   document owner, official URL, county/department, effective dates, superseded
   versions, checksum, access classification, and review status. Extend Week 4
   provenance to policy freshness and page/section citations accessible to users.
2. **Service-specific architecture and scope.** Define citizen information,
   staff-only retrieval, escalation, and any future transactional service separately.
   Record architecture decisions, API versioning, error contracts, and acceptance
   criteria before implementation. Do not reuse clinical decision rules.
3. **Production persistence.** SQLite queue code exists; no SQLAlchemy/Alembic/
   psycopg/asyncpg implementation was found in the scanned authored Python.
   Introduce an evaluated relational persistence approach, versioned migrations,
   ownership constraints, backup/restore tests, and transactional boundaries.
   PostgreSQL is a candidate, not a selected dependency.
4. **Permission-aware retrieval and answers.** Add access checks before retrieval
   and tool execution, approved document ingestion, corpus revision tracking,
   evidence-based abstention, and citation verification. Evaluate lexical/semantic
   baselines before deciding on hybrid retrieval or reranking.
5. **County evaluation program.** Build independently reviewed English/Kiswahili
   benchmarks covering fees, permits, departmental routing, obsolete/conflicting
   documents, unavailable evidence, injection, and cross-scope access. Measure
   retrieval recall, claim support, citation correctness, task success, cost, and
   latency separately. Keep train/development/held-out groups distinct.
6. **Provider reliability and spending controls.** Define deadlines, retryable
   failure classes, jitter/backoff, circuit breaking, cancellation, concurrency,
   token budgets, and observable fallback policies. Validate provider destinations
   and data handling before using external models.
7. **Operational deployment.** Add secrets management, identity integration,
   protected CI/merge rules, dependency/image scanning, restricted metrics, readiness
   distinct from liveness, service objectives, incident runbooks, and rollback drills.
   Workflow files cannot prove repository branch protection is enabled.
8. **Citizen privacy and safe tools.** Define data minimization and retention with
   county owners, scoped audit events, human escalation, and approvals/idempotency
   for any future action that changes a government record. Course regexes and
   hashes are building blocks, not proof of privacy or legal compliance.
9. **Optional multimodal intake.** [Week 5 transcription](../../venv/wk5/wk5_capstone/transcribe_audio.py)
   has provider calls, hash-based caching, and conservative unknown fields. Voice
   intake would additionally need approved uploads, size/type limits, access scope,
   retention, accessibility, and language-quality evaluation. It is outside the
   initial chatbot scope unless explicitly approved.

## Proposed next phase and review outcome

The strongest reusable foundation is modular configuration plus Week 6 API
contracts/authorization, Week 2 retrieval boundaries, Week 4 provenance, and Week 8
release gates. Keep a deterministic offline baseline like Module 4 while evaluating
live retrieval and LLM behavior. Reuse patterns through new county-specific code
and tests rather than copying whole projects or data.

The next proposed phase is architecture documentation: approved service scope,
trust boundaries, source governance, module responsibilities, evaluation criteria,
and deployment requirements. No implementation, dependency installation, push,
pull request, merge, or next-phase work is authorized by this report.

## Validation and preservation

Documentation validation checks all source links against files on disk, required
sections, Markdown fence balance, and Git whitespace. Only this report is staged
for the review commit; it contains source references and analysis, not copied
credentials or datasets. Coursework preservation is checked against an external
SHA-256 baseline excluding the official project repository. No coursework scripts
or tests are run, so there is no claim of passing application tests.

Validation result: all 49 source links and full source paths resolve; required
sections, fence balance, credential-pattern review, and Git whitespace checks pass.
The before/after comparison checked 213,646 files (including environment files and
Git metadata): zero added, zero removed, and zero content changes. The baseline and
comparison artifacts remain outside the project under `/tmp` and are not committed.
