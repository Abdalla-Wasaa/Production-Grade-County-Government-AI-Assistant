# Ollama adapter — P3-02

Status: implementation and mocked tests prepared; exact-exposure runtime approval is
still required. No Ollama installation, model download, live inference, generation
HTTP endpoint or conversation dispatch has run or been added by this milestone.
P3-01 merged in PR #31; its provider contracts are unchanged.

## Configuration and switching

Unconfigured application and all automated tests retain fake/fake-v1. For a separately
authorized **host-local** synthetic Ollama exercise, explicitly configure:

```dotenv
AI_PROVIDER=ollama
AI_MODEL=llama3.2:3b
AI_ALLOWED_MODELS='["llama3.2:3b"]'
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_CONTEXT_TOKENS=8192
AI_TIMEOUT_SECONDS=60
AI_MAX_RESPONSE_BYTES=65536
```

Provider selection never comes from a browser or generation request. To select a
reviewed, installed alternative such as llama3.2:1b, change AI_MODEL and the explicit
AI_ALLOWED_MODELS JSON list; no provider-interface, frontend or conversation-business
logic changes are needed. The allowlist accepts 1–32 unique explicit local model
tags. Unknown models/providers, untagged names and cloud model names fail closed.
The adapter never pulls or discovers a model automatically. `fake` still requires
model `fake-v1`; setting only AI_PROVIDER=ollama with the fake model is rejected.

Numeric loopback origins 127.0.0.1 and [::1] are the only supported hosts, over HTTP
or HTTPS, with a valid optional port. DNS names (including localhost), metadata/IP
aliases, userinfo, URL paths, query strings, fragments and encoded hosts are rejected.
Redirects and environment proxies/credentials are disabled; TLS verification remains
on. The path is fixed at /api/chat. Optional OLLAMA_API_KEY is a hidden SecretStr
bearer credential for an explicitly configured local gateway, never a URL or browser
setting. Do not introduce a production credential in this development environment.

Loopback is relative to the backend process: this does not wire a host daemon into
Compose or publish any model port. Existing isolated Compose networking is unchanged.
Use the same approved host/network context for a future local backend/model exercise;
container-to-host networking requires a separately reviewed design, not an SSRF bypass.
A malicious process on the same host could still impersonate a loopback service.

## Transport and result semantics

The factory adds Ollama behind the existing AIProvider protocol and ManagedProvider.
Construction/startup creates a client but does not contact or probe a model. Health
and PostgreSQL readiness retain their existing semantics. HTTP resources are closed
by the existing application lifespan/factory context, including failure paths.

[Ollama chat API](https://docs.ollama.com/api/chat) is called with stream=false,
keep_alive=0, bounded num_predict and the configured num_ctx. The request preserves
message roles/content; language is request metadata for future orchestration, not an
automatically invented system prompt. No tools, RAG, memory policy or prompt templates
are added. Unanswered persisted messages remain untouched.

Results retain exact configured/returned model identity, assistant text, stop/length
reason and available token counts. Missing token counts remain unknown. Synthetic
flag means fake-provider output, not the classification of the input data. A mocked
Ollama result identifies Ollama while its test inputs are still synthetic.

Reject mismatched model identity, malformed/incomplete JSON, invalid roles, nonempty
tool calls, blank/oversized output, impossible usage, non-JSON media and compressed
responses. Body reading stops at the configured byte cap, even without Content-Length.
Existing per-process concurrency and total deadline include admission waiting; the
adapter also bounds the transport and propagates cancellation while closing streams.
No retries, model downloads, redirects or provider fallback occur.

[Documented errors](https://docs.ollama.com/api/errors) map to fixed safe codes:
404 model_not_found, 429 provider_rate_limited, 5xx/connection failure
provider_unavailable, deadline/read timeout provider_timeout and other non-success
status provider_request_rejected. A 404 can also reflect a wrong local gateway route;
verify configuration rather than exposing upstream error details. Raw upstream bodies,
credentials, prompt content and transport exceptions are not explicitly logged or
included in public errors. This is not durable per-user quota or spend enforcement.

## Deterministic validation

`tests/test_ollama_provider.py` uses HTTPX MockTransport and synthetic streams only.
Tests prepare English/Kiswahili payloads, success/usage, missing models, unavailable
service, invalid configuration, SSRF rejection, malformed/oversized output, safe
errors, model switching, cancellation, stream/client cleanup and no sensitive logs.
The existing socket guard and fake-default fixture remain enabled. There is no model
server, model download or inference CI service; all seven CI workflows are unchanged.

Tests have not yet executed for this changed exposure. After explicit authorization,
run the focused Ollama cases, all existing fake-provider tests and the relevant backend
non-integration regressions. Preserve prior PG/frontend evidence where unaffected.
See [exposure assessment](P3_02_EXPOSURE_ASSESSMENT.md) for the exact next decision.

## Local model/server gate — not executed

The initial model is [Llama 3.2 3B](https://ollama.com/library/llama3.2:3b), an
instruction-tuned open-weight model under Meta's community licence, not OSI open
source. Review its licence/acceptable-use terms before installation. Its published
model download is approximately 2 GB; runtime RAM/VRAM is higher and depends on
quantization, context, concurrency and offload. Do not infer minimum hardware or a
latency SLA from download size. Record measured resources/latency on the approved
host before choosing limits. Kiswahili is not in the model's officially supported
language list; transport tests do not demonstrate actual Kiswahili response quality.

The API contract was reviewed against current vendor docs on 19 October 2026;
no installed Ollama server version has been verified. Before any separate live test,
review/record the chosen supported server version, model manifest/digest, local
hardware, loopback binding, cloud-disabled configuration and log/retention settings.
Use [Ollama FAQ](https://docs.ollama.com/faq) instructions to configure
OLLAMA_NO_CLOUD=1 and OLLAMA_HOST=127.0.0.1:11434 on the server. The client cannot
prove that a compromised/misconfigured local daemon will keep prompts local.

Only after explicit install/inference authorization: verify the selected server and
model identity, then send a bounded fictional synthetic request through this provider
boundary; record actual model, usage, cleanup and safe error behavior. No live test
command is executed or implicitly approved by this document. keep_alive=0 requests
unloading but is not proof of secure memory erasure; cancellation does not guarantee
immediate server/GPU resource release. Monitor server resource limits separately.

Current development acceptance expires 23 October 2026, 23:59 EAT and is not inherited
for this new exposure. No acceptance, baseline, inventory policy or historical record
is changed. No real citizen/county data, production credentials or deployment.
