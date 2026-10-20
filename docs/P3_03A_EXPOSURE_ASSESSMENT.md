# P3-03A source exposure assessment — runtime approval pending

[Issue #36](https://github.com/Abdalla-Wasaa/Production-Grade-County-Government-AI-Assistant/issues/36),
branch `feat/p3-03a-model-quality-remediation`, base main
`94e63822990841290f84a7637827a10ee0305917` (merged PR #35).
Source commit `ebb5a54`; prepared tests `0f9a3f8`; final documentation commit is
reported separately. Exact prepared application exposure:
`dc3e34e2151091e03e21d1929f28a6d6e0b0e0208604663dabef98b55d623780`.
Previous approved P3-03 exposure:
`95a4fcbaa568938334a96ba19eb10f868802c7f6ba26dfd20d4363b850b8bf00`.

## Scope and risk delta

See [root causes, design and pre-evaluation gates](P3_03A_REMEDIATION.md).
Source adds compact prompts, a server-owned default county abstention path,
completion classification, additive optional timing and honest report metrics.
No protocol methods, domain routes, SQL privileges, authentication, privacy policy,
provider allowlist, network bindings, dependencies or base-image pins change.
No model inference, model downloads or new source/runtime tests have run.

The default unverified-county policy does not call the model for any input; its
fixed bilingual response is a policy notice, never learned/model-quality evidence.
It intentionally abstains on general questions too. General-information generation
requires explicit server-owned selection. No client can claim verified context or
select that setting through PromptInput. An operator misrouting county requests
into general mode still risks hallucination/injection; do not expose a generation
API or treat this as reviewed county knowledge. No classifier is claimed secure.

Truncated and suspected-incomplete results expose no displayable answer. Raw partial
text remains private diagnostic evidence, not a completed response. Future callers
must honor the displayable property/status. Punctuation detection can both overflag
valid answers and miss fluent nonsense; it is not proof of completeness/factuality.
Provider-reported timings are diagnostic; wall deadline remains client enforced.
No keep-alive extension, automatic retry, prompt repair, privilege increase or new
outbound route is introduced. No success/failure or fee-quote flag is suppressed.

## Prepared tests and checks

36 new cases were enumerated statically, not collected or executed. They cover:
all 100 existing cases plus unseen input through fail-closed policy with a provider
that must not be called; bilingual isolation and explicit policy identity; invalid
routing; character cap; length finish and suspected partial status; private reports;
uncertainty/refusal signals; optional/zero/invalid durations; timeout/p50/p95 accounting.

The existing 38 orchestration cases now explicitly select general-information mode
so containment cannot mask provider regressions. Also prepare existing 43 provider,
68 mocked Ollama and 128 non-integration backend regressions: expected total 313
prepared cases, subject to actual authorized collection. Database/frontend evidence
is unaffected and must not be represented as newly executed. The fake-only runner
uses explicit general mode, reports status including suspected-incomplete marker
responses, and never silently substitutes policy output for model/fake evaluation.

Ruff, formatting, strict Mypy and repository documentation checks passed; redacted
secret scanning found no leaks. Runtime tests and live evaluation remain **unrun**.
The ordinary policy checker correctly stops with changed exposure / owner review
required; this is expected enforcement, not a reason to skip or weaken checks.

## Exact next authorization

Authorize isolated synthetic-only execution for the final reported commit and exact
exposure above: the 36 new cases, 38 existing orchestration cases, 111 provider/Ollama
cases, relevant 128 backend regressions and offline fake/policy evaluation.
Use mocks/fake only; no live Ollama calls/downloads, production or real data.
Any corrected exposure follows the existing runtime authorization rule before execution.

Actual human CRITICAL review is confirmed only for 19 October. The 20 October review
remains unconfirmed; before a runtime action requiring that daily review, obtain real
owner confirmation covering SQLite CVE-2025-7458, libxml2 CVE-2026-6653 and zlib
CVE-2023-45853 assessments in the vulnerability register. Do not record it from this
source authorization or invent a future review. Expiry remains 23 October 2026,
23:59 EAT; no extension, production, public Ollama or real citizen data.

After offline validation, obtain separate exact security-record/publication approval.
If findings/inventories remain unchanged, the anticipated minimum proposal is active
risk acceptance, byte-preserved P3-03 acceptance snapshot, this assessment, SECURITY.md
and AGENTS.md. None of those acceptance/snapshot updates is applied here. New findings,
fixes, severity/vendor/KEV changes or inventory changes require their own disposition;
never approve them from equal counts alone. Separate authorization is necessary for
any later live model evaluation; no P3-04 or automatic push/PR/merge is authorized now.

## Fresh packaging/security evidence

[Scan summary](security/p3-03a/scan-summary.json) and
[immutable image manifest](security/p3-03a/image-manifest.json) bind the exact source.
Full raw reports remain at `/tmp/county-p303a-scans` and dependency audits at
`/tmp/county-p303a-audit`; temporary local evidence is not hosted CI proof.
Packaging-only runtime image build passed without executing application modules.

| Image | HIGH | CRITICAL | Packages | Inventory changed |
| --- | --- | --- | --- | --- |
| Backend | 44 | 0 | 122 | No |
| PostgreSQL | 71 | 3 | 144 | No |
| Web | 0 | 0 | 21 | No |

Total 115 HIGH / 3 CRITICAL; exact finding-row comparison shows no new, removed or
altered occurrences/severities/vendor status, not merely equal totals. No reported
fixed versions or matches in the fresh retrieved KEV snapshot. Python runtime/dev
and tooling dependency audits report zero advisories. This does not prove new source
is vulnerability-free, and it is not automatic acceptance of the new exposure.
No baseline, inventory-policy, active/historical acceptance record or CI workflow
changed. Scans correctly fail policy acceptance because the old source hash differs;
complete raw image reports exist and are not treated as missing/clean evidence.

The three inherited CRITICALs remain SQLite CVE-2025-7458 (crafted SQL prerequisite,
no demonstrated API exploit), libxml2 CVE-2026-6653 (authenticated SQL/XML plausible
path, no reproduced exploit), and zlib CVE-2023-45853 (Debian says vulnerable MiniZip
is excluded; keep scanner finding). This module adds no SQL/XML, document parser,
permissions or domain paths. All existing assessments and daily review requirements
remain; no 20 October human review is asserted here.
