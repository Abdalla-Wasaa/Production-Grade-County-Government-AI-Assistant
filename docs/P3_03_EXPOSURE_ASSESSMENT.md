# P3-03 focused exposure assessment — runtime decision pending

Tracking: [issue #34](https://github.com/Abdalla-Wasaa/Production-Grade-County-Government-AI-Assistant/issues/34).
Implementation: `feat/p3-03-prompt-orchestration`. Source commit `98891ad`;
prepared tests/fixtures commit `3eb4fe6`; the final documentation commit is reported
separately. Exact exposure:
`95a4fcbaa568938334a96ba19eb10f868802c7f6ba26dfd20d4363b850b8bf00`.
Prior accepted P3-02 exposure:
`8e1fa66f0928b01552045590813ad04f971c29a3c443dd92358721ccdc27a41d`.

## Evidence and delta

Merged P3-02 PR #33 has all seven required PR checks passed. The starting main was
`d3dc9c1c4ce5e891c4cb9dd0b6bb99b565ca4892` and clean. No changes to existing
provider contracts/factory, authentication, conversation persistence, privacy,
HTTP routes, migrations, network permissions, base-image pins, dependencies or CI workflows.
No model downloads or inference occurred during this task.

New code adds versioned bilingual prompts, a bounded stateless orchestrator and
synthetic evaluation helpers. The provider remains owned by its existing context;
no generation endpoint is exposed. Input is capped at 4000 characters; output has
configurable token/character budgets, and a deadline at most 30 seconds. Evaluation
reports omit content and preserve unknown usage, failures and pending human review.
The evaluator's separately returned answer is synthetic, private review material,
not permission to log arbitrary user data.

Prompt injection and hallucination remain material model risks. Instruction
separation is defense in depth, not a guarantee. No verified county catalogue is
provided; unsupported official facts require abstention. Lexical evaluation flags
are incomplete and may flag disclaimers; independent bilingual semantic review is
required. The 100 development cases are not a reviewed held-out release benchmark.
Do not claim production quality or the full Phase 3 evaluation gate is complete.

[Fresh scan summary](security/p3-03/scan-summary.json) and
[immutable runtime manifest](security/p3-03/image-manifest.json) bind the final
packaging-only build. Full Trivy reports remain in `/tmp/county-p303-final-scans`
and dependency audits in `/tmp/county-p303-audit`; these temporary paths are not
hosted artifacts and must be regenerated/archived through normal authorized CI.
No changed application modules or tests were executed during packaging scans.

| Image | Packages | Inventory SHA-256 | HIGH | CRITICAL |
| --- | --- | --- | --- | --- |
| Backend | 122 | 3b313e4e52f23217faa9d0af79c3e339d2c4477aba1e6d66146dc1457c844aae | 44 | 0 |
| PostgreSQL | 144 | f0ff6951e8f3157a9f0e6d15387c68b6e4e591afd21d2d0da972c122ed1ad288 | 71 | 3 |
| Web | 21 | e9d19af8839b51cd311f6b527994b6cc624ee2b0491513c293f6fefa6cb60443 | 0 | 0 |

Complete occurrence comparisons against the accepted baseline show zero added,
removed or altered HIGH/CRITICAL rows, not merely equal totals. No reported fixed
versions or matches against the freshly retrieved KEV snapshot. Runtime and tooling
Python dependency audits report zero advisories. No new packages or lock changes.
These scanner observations do not prove that new application code is vulnerability-free.

The three existing PostgreSQL CRITICAL assessments remain individually tracked:

- CVE-2025-7458 / SQLite: crafted SQL prerequisite; no demonstrated API exploit.
- CVE-2026-6653 / libxml2: authenticated PostgreSQL SQL/XML is a plausible path;
  no reproduced exploit. The new stateless module adds no SQL/DB access.
- CVE-2023-45853 / zlib1g: Debian excludes vulnerable MiniZip from these binaries;
  retain the scanner finding and existing assessment.

See [the vulnerability register](VULNERABILITY_REGISTER.md). No new reachable path
to those packages is introduced by this module. This assessment does not reclassify
or accept them. Actual owner review confirmed for 19 October only; future required
daily reviews must be real, not inferred from this document.

## Validation status and precise next decision

Ruff, formatting, strict Mypy and repository documentation validation passed.
Source secret scanning passed. Prepared tests cover role separation, bilingual fake
responses, invalid configuration/input, bounds, cancellation/timeout cleanup,
normalized private errors, review signals, report privacy/identity, dataset coverage
and fake-only evaluation. Existing 43 provider, 68 Ollama and backend regressions
will be reused or rerun only where the new path/configuration isolation affects them.
**No new runtime tests or evaluations have run.**

The normal workflow-policy and image gates correctly reject changed exposure with
owner review required. Complete image reports exist; this is not a clean-policy pass
or missing-scan workaround. All seven checks and branch protection remain unchanged.

Required now: authorize isolated synthetic execution of this exact commit/exposure's
prepared orchestration tests, fake-only 100-case evaluation, existing provider tests
and relevant non-integration backend regressions. No network/model calls, downloads,
real data, public deployment or acceptance changes. Any corrected exposure must
follow the existing authorization procedure before executing changed code.

## Proposed later publication update — not applied or approved

Only after authorized tests pass, request a separate exact five-file decision:

1. `.github/security-risk-acceptances.json`: bind each unchanged inherited occurrence
   to the tested P3-03 exposure with explicit owner evidence; no expanded scope.
2. `docs/security/p3-03/p3-02-acceptance-snapshot.json`: preserve active P3-02 acceptance
   bytes and reconstruction hash unchanged before replacing the active record.
3. `docs/P3_03_EXPOSURE_ASSESSMENT.md`: record actual authorized results and decision.
4. `docs/SECURITY.md`: identify the new narrowly scoped development decision.
5. `AGENTS.md`: record exact owner approval and supersede pending statements only.

No baseline/inventory-policy change is proposed because all inventories/findings
are unchanged. Preserve expiry **23 October 2026, 23:59 EAT**, synthetic/local scope,
actual daily CRITICAL review, all fix/new-finding/severity/KEV/exposure/dependency
invalidation rules, complete scanning, seven required checks and protected PR review.
No automatic future-exposure approval, expiry renewal, merge, real citizen data,
live inference or production deployment. Nothing in this proposal changes acceptance.
