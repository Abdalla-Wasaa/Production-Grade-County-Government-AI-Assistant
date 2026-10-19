# P3-02 focused exposure assessment — runtime authorization pending

## Prerequisites and exact source

PR #31 is owner-merged at d66602dcd8c0ab46a33279ee7807b12954285ae8. All seven
required PR checks passed; main was synchronized with --ff-only from a clean tree.
Its separate merged-main runs were still pending/in progress when inspected during
source preparation; do not claim a new green merged-main run. P3-01 acceptance
validated before source edits and remains byte-unchanged; it does not cover P3-02.
Issue #32 and the owner's explicit P3-02 authorization permit source implementation.

Branch: `feat/p3-02-ollama-adapter`. Application source is committed in a9c3420;
prepared mocked cases are committed in 426f486. Subsequent documentation commits do
not alter application exposure. No changed-source tests, Pytest collection, model
installation/download, inference call or affected application startup has executed.
Only static checks, dependency audit and packaging-only image build/scans ran.

| Binding | Value |
| --- | --- |
| Prior approved P3-01 exposure | 54a7c2e7d075593f17107dd652edf035b28b7a399611f700c095bc5f1b04ecc4 |
| New P3-02 exposure | 8e1fa66f0928b01552045590813ad04f971c29a3c443dd92358721ccdc27a41d |
| Prior backend inventory | 119 packages; 7c9d236e62e9b96b9dfe7ca03dd92b1d999c6bacfb7fb8f67949a9790d88274e |
| New backend inventory | 122 packages; 3b313e4e52f23217faa9d0af79c3e339d2c4477aba1e6d66146dc1457c844aae |
| New backend image ID | sha256:7a99f7540bbce74f866f4e037141dbcdf18ae841505f9e90a89ab28415dac3e5 |

## Changes and newly introduced risks

Existing typed provider contracts and ManagedProvider semantics are unchanged.
The factory now selects fake or Ollama using validated server-owned configuration.
Default remains fake/fake-v1. Ollama uses explicit allowed models, initially
llama3.2:3b, through a bounded asynchronous /api/chat client. Configuration changes
can select another permitted model without editing domain/frontend code.

This introduces real new capability even with no new scanner findings: when opted
in and later authorized, prompts leave the backend process for a local inference
service; the HTTP parser/client, response validation, local service trust, optional
gateway credential, server logs/retention, model provenance and CPU/RAM/VRAM usage
require review. A compromised local service can return hostile data. The client
cannot prove a misconfigured local daemon will avoid cloud forwarding or logging.
No live model quality/resource claim follows from mocked tests or scans.

Controls: numeric 127.0.0.1/[::1] origins only; no DNS, userinfo, paths, query,
fragment, encoded host, redirect or ambient proxy/credential handling. TLS validation
remains enabled. Request-supplied endpoint/model overrides are absent. Allowlisted
explicit local model tags exclude cloud names. No discovery/download, retries,
provider fallback or tool dispatch. Output bytes/text/tokens, context, concurrency
and total deadline are bounded; model identity and response structure are validated.
Cancellation propagates and closes HTTP resources; server-side resource termination
still requires separate operational verification. Optional bearer key is SecretStr
and representations/logging avoid content/credentials. Server cloud disabling,
version/model manifests, log settings and loopback binding are prerequisites for any
future separately authorized live smoke test.

There is no new public API, authentication path, database schema/grant/query,
conversation mutation, frontend UI or Compose networking change. Startup/health
never probes or invokes Ollama. The existing SQLite CVE-2025-7458, libxml2
CVE-2026-6653 and zlib CVE-2023-45853 CRITICAL assessments remain tracked. This
adapter uses bounded Python JSON/HTTP parsing, not SQL/XML/SQLite or compressed
response processing; no additional direct path to those three defects was identified.
That focused assessment is not an exploit demonstration or proof of vulnerability-free
code. The owner's actual 19 October review is recorded separately; future daily
reviews remain mandatory, not automatically completed here.

## Dependency and complete scan evidence

HTTPX was already locked for development. Promoting it to runtime adds these exact
packages to the runtime image, with no resolved-version upgrades or removed packages:

| Runtime addition | Version |
| --- | --- |
| httpx | 0.28.1 |
| httpcore | 1.0.9 |
| certifi | 2026.7.22 |

[Dependency audit](security/p3-02/dependency-audit-summary.json) reports zero backend
and tooling advisories for the locked package sets. Python 3.12 compatibility is
resolved by the existing uv lock; actual adapter/runtime tests remain unexecuted.
No SDK or model-server dependency was added.

[Fresh scan summary](security/p3-02/scan-summary.json) and
[immutable manifest](security/p3-02/image-manifest.json) bind all three complete raw
reports, scanner/database freshness and the exact package/CVE comparison.

| Image | HIGH | CRITICAL | New/removed HIGH/CRITICAL occurrences | Available fixes / KEV matches |
| --- | --- | --- | --- | --- |
| Backend | 44 | 0 | 0 / 0 | 0 / 0 |
| PostgreSQL | 71 | 3 | 0 / 0 | 0 / 0 |
| Web | 0 | 0 | 0 / 0 | 0 / 0 |

Total 115 HIGH/3 CRITICAL remain exactly the inherited reviewed occurrence rows.
PostgreSQL and web full inventories/pins are unchanged; backend inventory changes
only by the three listed packages. No finding is suppressed, removed or reclassified.
No reported fixes or retrieved KEV matches; these are scanner facts, not assurance
that the new network code is flaw-free.

The unmodified normal policy scan correctly exits nonzero. Two distinct gates apply:
changed application exposure lacks an owner decision, and the backend inventory no
longer matches its approved 119-package reference. The scanner produced valid backend
JSON with a matching immutable image ID; the script's generic backend-evidence failure
label is caused by inventory validation, not a missing scan. No checker was weakened
or approved inventory/baseline/acceptance record changed. Raw reports remain outside
source control with hashes in the summary.

## Validation prepared and exact authorization requested

Static Ruff lint/format and strict Mypy pass. Dependency audit passes and secret and
documentation checks run before committing this assessment. There are 68 prepared
Ollama cases (static AST count, not executed results), plus the existing 43 provider
and 128 non-integration backend regression cases to run after authorization.
One existing defensive factory fixture now uses a genuinely unsupported provider
instead of Ollama, which is newly implemented; no existing contract assertion is
removed. Network denial and fake-default fixtures stay active. MockTransport and
synthetic streams cover success/bilingual payloads, optional usage, model switching,
missing model/service, malformed/oversized/compressed output, SSRF/invalid settings,
private errors/logs, cancellation, deadlines and resource cleanup.

**Next decision requested:** authorize isolated synthetic-only execution of this
exact source/exposure: 68 mocked Ollama cases, 43 provider cases and 128 backend
regressions. No actual Ollama daemon/model installation, downloads, inference or
external network calls are requested. Corrections changing exposure must follow the
existing exact-hash runtime authorization rule before corrected source executes.

This initial decision is testing-only, not permission to modify security records,
approve the changed inventory, push/open a PR, merge, renew expiry or run a live model.
After actual validation, request the minimum separate owner acceptance/inventory
record approval. Preserve the prior P3-01 policy bytes in a historical snapshot at
that later approved step. All seven CI checks, complete scanning, exact inventories,
logging/authorization/privacy controls and branch protection remain active.

Current expiry remains **23 October 2026, 23:59 EAT**. No real citizen/county data,
production credentials or production deployment. See the
[local guide](OLLAMA_LOCAL_DEVELOPMENT.md) for the separate server/version/model,
licence, resource and cloud-disabled prerequisites for future local Llama smoke tests.
