# P3-03D — Node build-toolchain remediation

Status: source patch and packaging-only analysis prepared; changed-environment
execution, acceptance changes and publication are not authorized. Tracking: issue
[#41](https://github.com/Abdalla-Wasaa/Production-Grade-County-Government-AI-Assistant/issues/41),
following issue #39. Baseline main/merged PR #40 is
`770f7be542ff33610ade77dfca1da43caae14734`.

## Root cause and bounded remedy

Node's immutable build-stage image contains Debian `perl-base` and a bundled npm
installation. npm's own transitive dependencies include `brace-expansion`, `undici`
and `http-cache-semantics`. These are not direct application dependencies or entries
being upgraded in the frontend dependency graph. The Node image is used for test and
build stages; the final web image copies only compiled frontend assets into the
unchanged Nginx runtime. CI also explicitly selected the affected npm 11.19.1.
Build-stage-only packages still matter: the builder processes project inputs and
produces distributable assets; local use does not eliminate this attack surface.
Scanner findings do not independently establish an exploitable application path.

Retain Node 24.22.0 and use its vendor-patched Bookworm image. Replace the entire
bundled npm installation with official npm 11.21.1, verified before extraction.
Do not overlay individual npm internals or run vulnerable npm to install its own
replacement. Use the same archive/checksum in Docker and all three CI bootstrap
steps. The CI command policy now requires that bootstrap as well as the exact npm
version; no existing validation commands or required contexts were removed.

| Item | Previous | Proposed |
| --- | --- | --- |
| Node index digest | `sha256:a5f4366e834695d5f363b920c104953a535d3a9864d1bdf74566a0ebe01daee5` | `sha256:91acba91b842bec0bf7ea6f5e09c644c7ccad72c4996ed9616d861d1c7cd60d4` |
| amd64 child | `sha256:ec857ea6bb60cb3d0fa4d97495590c5fe7d51be8572c307b55957eeb06569cf7` | `sha256:a8efdaa8f2458a83ad61c9b8e957c94c2312a9e60604d5b9b093cf89ad9f5984` |
| perl-base | `5.36.0-7+deb12u3` | `5.36.0-7+deb12u4` |
| npm | `11.19.1` | `11.21.1` |
| bundled brace-expansion | `5.0.9` | `5.0.12` |
| bundled undici | `6.28.0` | `6.29.0` |

Official npm archive:
`https://registry.npmjs.org/npm/-/npm-11.21.1.tgz`.
SHA-256: `dd77c48eb845f4856c2cdba347cfb52bd877a2655a1ea48ff0c4796e3df9dd7b`.
Registry SHA-512 integrity was also checked during preparation. npm 11.21.1 supports
Node `^20.17.0 || >=22.9.0`. Inspected npm 11.20.0 and 11.21.0 still bundled the
vulnerable brace-expansion/undici versions. npm 12 is unnecessary.
See the [official release](https://github.com/npm/cli/releases/tag/v11.21.1)
and [registry metadata](https://registry.npmjs.org/npm/11.21.1).
The complete official npm bundle changes its internal dependencies; this is not a
claim that only two files inside npm change. The committed scan comparison records
complete scanner-discovered package inventories. Frontend lock entries other than
the root npm engine declaration remain byte-for-byte unchanged.

## Packaging-only scan evidence — 21 October 2026

[Static scan comparison](security/p3-03d/static-scan-comparison.json) retains all
HIGH/CRITICAL occurrences, full scanner-discovered package inventories, raw report
hashes, KEV snapshot version and candidate provenance. Raw reports and the synthetic
archive remain outside Git in `/tmp/county-p303d/` and the 21 October private
handoff tag-triage directory. No weights, caches or large archives are committed.

| Scanned filesystem | HIGH | CRITICAL | Fixable HIGH/CRITICAL |
| --- | ---: | ---: | ---: |
| Previously pinned Node base | 64 | 4 | 10 |
| Vendor-patched Node base alone | 60 | 1 | 3 |
| Vendor base + complete npm 11.21.1 replacement | 56 | 1 | 0 |

Removed CRITICAL Perl findings: CVE-2026-13221, CVE-2026-42496 and CVE-2026-8376.
Removed HIGH Perl findings: CVE-2026-42497, CVE-2026-48962, CVE-2026-57432 and
CVE-2026-57433. Removed npm findings: brace-expansion CVE-2026-102276 and
CVE-2026-102278; undici CVE-2026-19534; http-cache-semantics CVE-2026-93748.
There are no new HIGH/CRITICAL package/CVE occurrences in this comparison.
CVE-2026-9538 remains HIGH in Perl with a deferred vendor fix. The remaining builder
CRITICAL is zlib CVE-2023-45853; retain the finding and Debian's MiniZip applicability
qualification. No reviewed HIGH/CRITICAL identifier matches retrieved CISA KEV
catalogue version 2026.10.20. Absence from KEV is not proof of non-exploitation.

Method: fetch and verify immutable registry config/layers, decompress verified
layers, append a whiteout plus the official checksum-verified complete npm bundle,
then scan a synthetic Docker archive with Trivy 0.76.0, `--list-all-pkgs`, vulnerability
scanning and empty config/ignore files. No image was loaded or executed. This
validates a proposed filesystem composition, **not an actual Dockerfile build**.
The actual authorized build must be scanned again before declaring remediation
complete. No findings were suppressed. Retained findings require explicit review;
builder counts must not be confused with the deployed runtime totals.

## Compatibility and unchanged controls

No app-source, provider, model, prompt, benchmark, auth/privacy, Nginx configuration,
PostgreSQL pin or frontend dependency-tree upgrade. Node remains 24.22.0. npm stays
on major 11. Docker needs BuildKit support for `ADD --checksum`; fail rather than
fall back to an unverified download. The installer uses HTTPS with verification,
checks the pinned archive before extraction and preserves npm/npx entry points.
It requires write access to the dedicated Node installation prefix. Root is used
only to install the builder toolchain; project installation/build remains `node`;
the final web runtime remains UID/GID 101. Hosted Actions uses its isolated setup-node
prefix. Never run this bootstrap against unrelated coursework/system environments.

## Exact authorization boundary and validation plan

Previous accepted exposure:
`8fb62f79a81d7d1216126f0b4ff40fb38a9e3d01b625646b121bcb83e5b00c9f`.
Prepared exposure:
`015755bffa0f038986d719624979b317cb5e5527dceed76447fd207d09747ab1`.
The final source commit is reported with this assessment; documentation commits do
not alter the hash. No changed Node/npm/bootstrap, npm install, frontend build or
application test has executed. Only static policy tests, shell parsing and packaging
scans have run. Tests cover matching archive/version/engine pins, unchanged runtime
identity, checksum-before-extraction and six remove/no-op workflow mutations.

Request owner authorization for isolated synthetic validation of the exact final
commit/hash: actual BuildKit dependencies/test/build targets; bootstrap checksum
rejection and successful Node/npm version checks in a disposable prefix; frozen
`npm ci`, `npm ls --all`, `npm audit --audit-level=high`, lint, formatting, typecheck,
unit/JUnit, production build, relevant browser/accessibility and Compose smoke
checks; fresh builder and final-web vulnerability/package inventory scans; unchanged
backend/database evidence reused where valid. Never execute the superseded affected
builder for comparison. No live model calls, public exposure or real data.

## Security records and renewal

No acceptance, baseline, inventory, historical snapshot or AGENTS.md was edited.
Existing runtime evidence remains backend 44 HIGH, database 71 HIGH/3 CRITICAL and
web zero HIGH/CRITICAL; those images have not been rebuilt during this task.
Changed-build execution and final runtime counts remain to be verified. The old
acceptance does not cover this exposure. Its expiry remains **23 October 2026,
23:59 EAT**. The confirmed human review is 20 October; 21 October is not confirmed.

After authorized validation, propose a separate exact diff for the active
`.github/security-risk-acceptances.json`, byte-preserved historical snapshot,
this assessment, `docs/SECURITY.md` and `AGENTS.md`. Rebind only reviewed occurrences
to the final exposure. Update `.github/security-baseline.json` or
`.github/security-inventory.json` only if actual fresh runtime evidence requires
it and the owner approves the exact delta. Do not automatically accept residual
builder findings or add them to the runtime baseline; present their separate scope
and any proposed build-stage policy/inventory tracking for owner review.
Any renewal beyond 23 October needs a separately approved decision and exact diff,
current scans/fix/KEV checks and actual human CRITICAL review. No automatic renewal.

The Node renewal blocker is **not yet resolved**: static candidate evidence removes
the identified fixable findings, but actual build/runtime validation, final scans,
exact-exposure acceptance and required human review are outstanding. Preserve all
seven hosted contexts, their app binding and branch protection. No push/PR until
publication conditions are satisfied. No production, real data or public Ollama.
