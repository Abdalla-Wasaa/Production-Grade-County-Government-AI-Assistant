# AI provider foundation — P3-01

Implementation is prepared; runtime authorization and passing mocked tests are still
required. There is no generation HTTP endpoint or conversation dispatch in this
milestone. Authentication, ownership, retention and privacy controls remain authoritative.
This provider boundary is not a safety, billing or legal-policy enforcement layer.

## Configuration and model selection

No implicit dotenv file is loaded. Export environment variables or pass a private,
explicit environment file using the existing uv workflow. Safe default:

```dotenv
AI_PROVIDER=fake
AI_MODEL=fake-v1
```

The initial real local model is Meta Llama 3.2 3B Instruct through Ollama. Only after
separate synthetic runtime/inference authorization, configure the host backend:

```dotenv
AI_PROVIDER=ollama
AI_MODEL=llama3.2:3b
OLLAMA_BASE_URL=http://127.0.0.1:11434
```

This change performs no model install, pull or inference. Missing models fail safely;
the adapter never downloads one. Model installation, vendor licence/acceptable-use
review, resources and live smoke inference require their own authorized local setup.
Llama is open-weight under Meta's community licence, not OSI open source. The
[Ollama catalogue](https://ollama.com/library/llama3.2) describes the instruction-tuned
model and officially supported languages; Kiswahili is not on that list. Bilingual
mocked contracts are not evidence of actual Kiswahili answer quality.

The server-owned model registry defaults to fake/fake-v1 and ollama/llama3.2:3b.
To switch to another reviewed installed Llama model, change configuration only:

```dotenv
AI_PROVIDER=ollama
AI_MODEL=llama3.2:1b
AI_MODEL_REGISTRY='{"fake":["fake-v1"],"ollama":["llama3.2:3b","llama3.2:1b"]}'
```

Explicit tags and registry membership are required; untagged/cloud model names,
unknown providers and request-controlled model/endpoint overrides are rejected.
A mutable upstream model tag is not an immutable model identity: before authorized
live use, operators must record and review the installed model manifest/version.
Changing models can change resources, safety and language quality; configuration
capability does not automatically approve those changes.

| Variable | Default / bound | Purpose |
| --- | --- | --- |
| AI_PROVIDER | fake; fake or ollama | Provider factory selection |
| AI_MODEL | fake-v1 for fake; llama3.2:3b for ollama when omitted | Selected allowlisted model |
| AI_MODEL_REGISTRY | JSON provider-to-model lists, at most 32 unique entries per provider | Explicit operator model registry |
| OLLAMA_BASE_URL | http://127.0.0.1:11434 | Loopback-only origin, no credentials/path/query/fragment |
| OLLAMA_API_KEY | absent; SecretStr, hidden from representations | Optional loopback gateway bearer credential, never frontend configuration |
| AI_TIMEOUT_SECONDS | 60; greater than zero, at most 120 | Total deadline including admission, generation and body transfer |
| AI_MAX_OUTPUT_TOKENS | 512; 1–1024 | Reject requests above this output cap |
| AI_MAX_RESPONSE_BYTES | 65536; 1024–262144 | Bounded non-streaming JSON response |
| AI_MAX_CONCURRENCY | 2; 1–4 | Per-process concurrent transport calls; admission uses same deadline |

Loopback is relative to the backend process. Host backend and Ollama must share the
approved local network context. This milestone does not attach Ollama to Compose,
publish a model port, accept arbitrary remote URLs or change network isolation.
Before any live use, configure the Ollama server to disable cloud operation
(`OLLAMA_NO_CLOUD=1`), ensure local-only model provenance and loopback binding.
The client cannot prove how a compromised/misconfigured local daemon handles data.

## Contracts, lifecycle and extension

`app/modules/ai/contracts.py` defines the async `AIProvider` protocol, immutable
bounded Pydantic message/request/result/usage models and fixed-code `ProviderError`.
Requests have 1–32 messages, 8000 characters per message and 24000 total characters;
the last message must be a user message. These are engineering bounds, not proof
of tokenizer/context-window fit. The orchestration/token-budget layer remains future
work. The adapter uses an 8192-token context option and bounded output requests;
no prompt templates, catalogue, memory coordinator, RAG or tool dispatch is added.
Language is metadata for the future orchestrator; the adapter forwards the supplied
messages rather than silently inventing a language/system prompt.

`provider_context` selects fake or Ollama from validated settings. FastAPI's existing
lifespan owns and closes the provider, including cleanup on startup/shutdown failure.
Construction/startup makes no inference or discovery call. Health/readiness stays
independent of Ollama; database readiness semantics are unchanged. Future OpenAI,
Azure and Bedrock adapters should implement the same protocol and shared contracts,
with reviewed configuration and dependency/exposure changes, without altering
frontend or conversation business logic. No such adapters are implemented here.

The fake returns fixed, visibly synthetic English/Kiswahili text without echoing
messages; token usage is unknown, not fabricated. Ollama calls
[POST /api/chat](https://docs.ollama.com/api/chat) with `stream: false`, explicit model,
message roles and bounded `num_predict`. Result metadata retains provider and returned
model, measured token counts and finish reason. Mismatched models, malformed/partial
responses, unexpected tool calls and oversized or compressed responses are rejected.
There are no redirects, ambient proxy credentials, remote fallbacks or automatic retries.
Cancellation propagates and closes the response; deadline/connection errors become safe
codes. [Ollama status semantics](https://docs.ollama.com/api/errors) inform missing-model,
rate-limit, unavailable and rejected-request mappings. Upstream bodies and transport
exception strings are not retained in public errors or explicitly logged.

Per-process concurrency and generation caps are not durable user quotas, spend limits
or global multi-worker admission control. Those remain later orchestration work before
user-facing generation. `retryable` is advisory metadata; callers must not infer that
ambiguous generation can safely be retried without durable attempt contracts.

## Validation and security boundary

Tests in `backend/tests/test_ai_providers.py` use HTTPX MockTransport only. The existing
autouse fixture clears AI/OLLAMA environment variables and sets fake/fake-v1; the
existing socket guard remains active. No CI model downloads, Ollama daemon/service,
live inference or real credentials are introduced. No workflow controls change.

After exact-exposure runtime authorization, run the existing backend quality gates
and `pytest -q -m "not integration" --junitxml=.artifacts/unit.xml`. Shared tests cover
fake/Ollama and both languages; negative cases cover malformed/oversized responses,
HTTP failures, endpoint validation, configuration/model switching, deadline,
cancellation, bounded concurrency, shutdown and safe metadata/logging.

HTTPX is promoted from the existing locked development dependency to runtime; no
resolved version is upgraded. Its runtime transitive-package inventory still needs
fresh inspection and separate owner approval where policy requires it. Do not reuse
Phase 2 acceptance for this changed exposure. Existing scanning, exact inventories,
seven checks and branch protection remain enforced. Synthetic-only scope and
23 October 2026, 23:59 EAT expiry are unchanged; no production or real citizen data.
