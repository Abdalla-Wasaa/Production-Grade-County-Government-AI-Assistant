# AI provider foundation — P3-01

Issue #30 now limits P3-01 to the typed boundary and deterministic fake. Ollama and
Meta Llama 3.2 3B Instruct are deferred to P3-02. No model download, inference HTTP
client, external AI call, generation endpoint, prompt orchestration, schema change
or frontend integration is included.

## Configuration

```dotenv
AI_PROVIDER=fake
AI_MODEL=fake-v1
AI_TIMEOUT_SECONDS=5
AI_MAX_OUTPUT_TOKENS=512
AI_MAX_CONCURRENCY=2
```

Defaults are safe for both local development and automated tests. `AISettings` uses
existing Pydantic Settings conventions: no implicit dotenv discovery, frozen validated
settings, unknown choices rejected and input values hidden in startup errors. The
factory registry contains only implemented providers; currently only fake/fake-v1 is
valid. Ollama, OpenAI, Azure OpenAI and Bedrock selections fail safely rather than
falling back or causing an unexpected network request.

Timeout must be greater than zero and at most 120 seconds; output cap is 1–1024,
concurrency 1–4 per process. Requests above the configured output cap are rejected
before adapter invocation. Tests explicitly clear AI/OLLAMA environment variables
and select fake/fake-v1; the existing socket-denial guard remains active.

Future model switching belongs in server-owned validated adapter settings/registry,
not user input or conversation/frontend business logic. Once P3-02 implements and
approves Ollama, its intended local configuration is AI_PROVIDER=ollama,
AI_MODEL=llama3.2:3b and OLLAMA_BASE_URL=http://127.0.0.1:11434. **These choices are
not active or supported by P3-01.** No endpoint, credential or model-registry setting
for an unimplemented adapter is added here. A future model change requires the
applicable resource, quality, privacy and exposure review; configurability is not
an automatic security approval.

## Typed boundary and resource ownership

- `contracts.py`: async `AIProvider`, immutable Pydantic messages, request, model
  identity, response and usage contracts; fixed safe error codes and retryability.
- `settings.py`: supported provider/model selection and bounded execution settings.
- `fake.py`: deterministic, visibly synthetic English/Kiswahili replies without
  echoing prompts; unknown token usage remains `None`, never invented measurements.
- `factory.py`: explicit implemented-provider registry and `ManagedProvider` for
  total deadline, bounded concurrent adapter calls, safe exception normalization
  and lifecycle closure.

Requests have 1–32 messages, 8000 characters per message and 24000 total characters;
only system/user/assistant roles are accepted and the final message is from the
user. Language is en/sw. Responses identify the actual configured provider/model,
usage when known and stop/length reason. Managed execution rejects mismatched model
identity. These bounds are not tokenizer/context-fit guarantees or durable quotas.

The protocol has only `generate(request)` and `aclose()`; future adapters implement
it without exposing vendor types to domain callers. The existing FastAPI lifespan
owns the configured provider and closes it on exit, including startup/caller failure.
No provider call is made at construction, startup or by health checks. PostgreSQL
readiness and authentication/conversation/privacy APIs are unchanged.

The deadline includes admission waiting and generation. Cancellation propagates,
releases the concurrency permit and does not become a retryable generic error.
Timeouts and unexpected adapter exceptions become fixed codes without leaking raw
upstream exception text. Provider responses are not retried automatically. Future
real adapters must also honor cancellation/deadlines and close their own resources;
this wrapper cannot forcibly stop synchronous blocking work in a noncompliant adapter.

The fake has explicit constructor-only delay/failure injection for synthetic tests.
Those options are not environment settings or API request fields. Production-facing
fault controls are not introduced. No provider code logs messages or credentials;
request/response representations hide content. Actual synthetic content is still
sensitive test material for logging purposes and must not be echoed into reports.

## Verification and remaining gates

Prepared tests cover deterministic success in both languages, shared metadata,
invalid provider/model/parameters, fault codes, deadline/admission/cancellation,
unknown failure sanitization, lifecycle closure and no-network/no-private-logging
behavior. Mocked adapters verify the boundary independently of the fake.

After exact-exposure runtime authorization, run the existing backend quality gates:

```bash
cd backend
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked mypy
uv run --locked pytest -q -m "not integration" --junitxml=.artifacts/unit.xml
```

Owner-authorized testing passed 43 provider cases and 128 backend regressions;
see the [P3-01 assessment](P3_01_EXPOSURE_ASSESSMENT.md) for exact provenance and
the separate security-record approval still needed before publication. Runtime
packages and locks are unchanged from Phase 2. All seven checks, complete scans,
exact exposure/inventory enforcement and branch protection remain mandatory.
Synthetic local development only; no real citizen data or production deployment.
Existing acceptance expires 23 October 2026, 23:59 EAT and does not automatically
cover P3-01. No acceptance records or historical approvals are modified here.

P3-02 can add the local Ollama adapter, reviewed model settings, safe HTTP behavior
and mocked transport tests in its own branch/PR after this boundary is reviewed.
Model installation and live synthetic inference need separate authorization.
