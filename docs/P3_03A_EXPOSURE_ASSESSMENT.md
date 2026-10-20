# P3-03A source exposure assessment — publication approval pending

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
No live model inference or downloads occurred. The owner subsequently authorized
exact-source synthetic runtime validation; actual results are recorded below.

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
secret scanning found no leaks. Runtime validation is now complete under explicit owner authorization; live
evaluation remains unrun.
The ordinary policy checker correctly stops with changed exposure / owner review
required; this is expected enforcement, not a reason to skip or weaken checks.

## Authorized runtime outcome

Owner authorization covered commit
`1d1331d5542eb81d77cd4ccd33d2d0a9b19dc77c` and the exact exposure above.
No application/test defect or source correction was encountered. Actual tests:

- **185 passed**: 36 new remediation, 38 orchestration, 43 provider, 68 mocked Ollama.
- **128 passed** existing non-integration backend regressions; 79 PostgreSQL cases
  deliberately deselected and not claimed as newly run.
- **313 total tests passed**, no failures or skips among selected cases.
- Ruff, formatting, strict Mypy, documentation, sanitized report and secret checks passed.
- Existing TestClient emits one dependency deprecation warning per pytest invocation;
  no new dependency or unrelated change is warranted for that warning.

[Provider tests](security/p3-03a/provider-tests.xml) and
[backend regressions](security/p3-03a/backend-regressions.xml) are actual sanitized
JUnit evidence. The report below records two separate offline runs, not 200 model
inference calls. [Fake results](security/p3-03a/offline-fake-evaluation.json) and
[policy results](security/p3-03a/offline-policy-evaluation.json) retain all case IDs.

| Metric per language | Policy English | Policy Kiswahili | Fake English | Fake Kiswahili |
| --- | --- | --- | --- | --- |
| Cases executed | 50 | 50 | 50 | 50 |
| Policy-handled | 50 | 50 | 0 | 0 |
| Fixed fake responses | 0 | 0 | 50 | 50 |
| Real-model responses | 0 | 0 | 0 | 0 |
| Timeouts / provider errors | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 |
| Suspected incomplete | 0 | 0 | 50 | 50 |
| Claim flags | 0 | 0 | 0 | 0 |
| Uncertainty signals on expected cases | 36/36 | 36/36 | 0/36 | 0/36 |
| Character compliance | 50/50 | 50/50 | 50/50 | 50/50 |

The fixed fake marker lacks terminal sentence punctuation, so the conservative
completeness detector flags all fake outputs. Those completion failures are visible;
there are zero provider/harness evaluation errors. Neither run constitutes semantic
acceptance. The policy path intentionally abstains on general questions too and
cannot establish useful-answer quality. Zero claim flags proves neither truth nor
injection resistance. Fake/policy microsecond timings are implementation overhead,
not evidence that Llama's CPU latency or Kiswahili capability improved. All model
quality, human review and representative latency gates remain unmet/unverified.

## Exact next approval — records and publication only

Approve the narrowly scoped P3-03A synthetic-development decision for the final
reported commit with unchanged exact exposure above, through 23 October 2026,
23:59 EAT. Proposed changes are limited to these five files:

1. `.github/security-risk-acceptances.json`: bind the unchanged individually listed
   115 HIGH/3 CRITICAL occurrences and exact baseline to this tested source exposure;
   retain every invalidation trigger and production prohibition.
2. `docs/security/p3-03a/p3-03-acceptance-snapshot.json`: preserve the current P3-03
   acceptance bytes and reconstruction hash unchanged before replacing active binding.
3. `docs/P3_03A_EXPOSURE_ASSESSMENT.md`: record the actual owner decision/results.
4. `docs/SECURITY.md`: document the exact new restricted development decision.
5. `AGENTS.md`: supersede pending P3-03A record/publication statements for this hash only.

No inventory or vulnerability-baseline update is needed: all exact packages/findings
remain unchanged. No records or snapshots above have been altered. Publication
approval should explicitly authorize pushing this branch, opening the prepared PR
linked to #36, and running all seven hosted checks. It grants no model-quality
acceptance, future exposure approval, expiry extension, live inference, public
network exposure, real citizen data, production deployment or automatic merge.

Actual human CRITICAL review is confirmed only for 19 October. The 20 October review
remains unconfirmed; before a runtime action requiring that daily review, obtain real
owner confirmation covering SQLite CVE-2025-7458, libxml2 CVE-2026-6653 and zlib
CVE-2023-45853 assessments in the vulnerability register. Do not record it from this
source authorization or invent a future review. Expiry remains 23 October 2026,
23:59 EAT; no extension, production, public Ollama or real citizen data.

After offline validation, obtain separate exact security-record/publication approval.
Findings/inventories are confirmed unchanged; the exact minimum proposal is listed
above. None of those acceptance/snapshot updates is applied here. New findings,
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

## Security evidence confirmation after validation

Revalidated the complete existing packaging reports against immutable image IDs,
full inventories and exact finding rows for unchanged source. The reports were
scanned 20 October 2026 14:43 UTC using the database updated 20 October 13:14 UTC;
no rebuild was needed because source/dependencies are unchanged. No reported fixes
or KEV matches. Runtime/dev and tooling audit report hashes and zero-advisory results
were verified. Ruleset 25222082 was fetched directly: active, strict synchronization,
all seven contexts bound to Actions app 15368, no bypass actors; deletion/force pushes
remain blocked. No workflow, ruleset, historical acceptance or privacy control changed.
The normal exposure policy still correctly rejects the old acceptance for this hash;
its rejection must be resolved only by the separately approved record update.
