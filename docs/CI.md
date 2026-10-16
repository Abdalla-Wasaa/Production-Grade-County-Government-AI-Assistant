# CI quality and security gates

P1-05 PR #13 is merged; its audit remediation remains pending review.
P1-05 implements PR checks; it does not configure GitHub rules or authorize merging,
P1-06, deployment or real data. Required contexts must be selected in the remote
ruleset after their actual emitted names and results are verified on the PR.

## Architecture and contexts

The existing four workflows remain, with one separate scheduled monitor. Every PR
runs the seven contexts below without path filters, job conditions or matrices that
could remove or rename a gate. Pushes to main and manual dispatch also run them;
feature pushes are covered through their PR, avoiding duplicate push/PR runs.

| Context | Workflow | Validation |
| --- | --- | --- |
| backend-quality | backend.yml | Python 3.12, uv lock/compatibility, Ruff, scoped strict Mypy, 65 unit tests and JUnit |
| postgresql-integration | backend.yml | Digest-pinned PostgreSQL 17 Bookworm, 12 migration/readiness/session/privilege tests, packaged migration build |
| python-dependency-audit | backend.yml | Exact runtime/dev backend lock export and hash-locked repository tools; no skipped dependency records |
| frontend-quality | frontend.yml | Node 24.22.0/npm 11.19.1, npm ci/audit, ESLint/format/strict types, 27 unit tests, build, 48 browser/axe tests |
| compose-integration | compose.yml | Container unit tests, full disposable acceptance, one Chromium smoke through Nginx, complete image reports and risk policy |
| repository-quality | documentation.yml | Repository boundary/forbidden artifacts/docs/YAML, CI policy, regression tests, formatting and JUnit |
| secret-scan | documentation.yml | Real Gitleaks engine self-test with an ephemeral nonfunctional pattern; full history/current source scans |

Counts describe the initial P1-05 suite, not permanent limits. Required suites must
execute tests: absent, empty, failed or entirely skipped JUnit reports fail checks.
Axe catches automated WCAG issues; it is not a full accessibility certification.
The Compose browser test complements the existing standalone three-browser suite.

## Reproducibility and trust

Backend application dependencies use uv.lock. Repository/audit tools use
requirements-ci.lock, generated from requirements-dev.txt with uv pip compile
--generate-hashes; installs require hashes. The Linux x86-64 uv bootstrap wheel also
has a committed hash. Mypy 2.4.0 checks only backend/app with strict mode and the
Pydantic plugin. No blanket excludes or ignore_missing_imports are configured.
A numeric logging guard was rewritten with equivalent exact-type checks so Mypy
can narrow it; logging policy and secret redaction remain unchanged.

Actions are pinned to reviewed full SHAs. The workflow policy verifies the approved
source/pin pairs, unique contexts, unfiltered PR events, read-only permissions,
nonpersisted credentials, bounded hosted runners, artifact scopes and safe cache
writes. It rejects conditional quality steps and obvious publishing patterns.
No pull_request_target, workflow_run, production secrets, OIDC or deployment jobs
are used. PR code still executes untrusted code, including install/build hooks;
only ephemeral GitHub-hosted runners are supported. The owner reviews workflow,
policy, risk-decision and lock changes before merge. A policy file is not a
cryptographic proof of owner approval, and PR code can attempt to edit its own
checks; GitHub settings and human review remain necessary trust boundaries.

Caches contain downloaded uv/npm packages, never venvs, credentials or database
state. Keys include OS and dependency/tool lock hashes. Explicit cache saves occur
only on trusted main pushes; PRs may restore package archives. No broad restore
prefixes or shared Docker credential caches are used. Locks and hashes validate
install inputs even on cache hits. Exact pins need reviewed security refreshes.

## Vulnerability decisions

scripts/scan_images.py scans each final runtime once and retains full JSON,
including lower severities and all unfixable HIGH/CRITICAL findings. It evaluates
that same snapshot against .github/security-baseline.json and the explicit decisions
in .github/security-risk-acceptances.json. No Trivy ignore list or VEX suppression
is applied. The baseline is evidence, never approval.

The gate fails for a fixable HIGH/CRITICAL record, a new package/CVE/version/base-pin
combination, changed severity, any matching CISA KEV entry, missing/malformed
reports, unavailable/stale KEV or Trivy metadata, or absent/expired acceptance.
The source baseline records immutable base pins and actual report/image hashes;
rebuilt application image IDs are recorded but are not expected to be bit-identical.
Known accepted findings remain visible in reports and decision failures/summaries.

The acceptance envelope has production_allowed=false. A decision must include scope
synthetic-local-development, actual approved_by and approval_reference, reason,
approved_at, expires_at, baseline_sha256 and exposure_sha256. The latter binds
application code, dependencies, image build definitions and Compose/infrastructure
files, so changed exposure invalidates the decision pending owner review. Unknown fields,
missing approvals, future approvals, expired dates, changed evidence or acceptance
longer than 30 days fail. No permissive default or automatic renewal exists. An
empty decision list deliberately makes residual image findings fail. The owner
must explicitly approve the concrete evidence before an engineer records a decision.
New fixes, KEV entries and changed findings override even an unexpired acceptance.
An exposure change requires immediate owner reassessment; code cannot infer every
change in real-world reachability, so review is also mandatory.

KEV is retrieved from the CISA-maintained mirror, with a seven-day maximum catalogue
age; stale/unavailable evidence fails closed. Trivy metadata must be no older than
48 hours. Full feed/database provenance and scan timestamps accompany reports.
No KEV match means no match in that catalogue, not proof of no exploitation.
Python dependency audits currently fail on any advisory and do not inherit OS risk
acceptance. Frontend npm audit continues to fail at HIGH or greater.

See [the vulnerability register](VULNERABILITY_REGISTER.md). All public/production/
real-data deployment remains blocked, independently of a development CI result.

## Scheduled monitoring

security-monitor.yml runs daily at 06:00 UTC / 09:00 EAT and on manual dispatch.
It audits Python/frontend dependencies, checks Docker Hub/GHCR tag manifest hashes
against pins, builds current pinned runtimes and invokes the same image policy.
Changed digests are reported as actionable failures; nothing is upgraded silently.
It never runs migrations, starts database containers, resets volumes, rotates
credentials, publishes images or deploys. It is informational to individual PR
required-check selection; a failed monitor still requires owner investigation.
The timer activates after this workflow is merged into the default branch. Before
then the script is testable locally and workflow dispatch availability is limited
by GitHub's default-branch discovery rules.

## Reports and investigation

JUnit reports are validated and stripped of payloads before upload; failures still
fail jobs. Browser traces/screenshots contain synthetic UI data only and are kept
seven days. Test/dependency/image reports are retained fourteen days. Compose
failure diagnostics contain status/exit/health/restart counters and a failure class,
not raw logs, inspect environments, secrets or volume contents. The raw full scan
reports contain public package/advisory evidence; no runtime secret mounts are
part of images or scan inputs. Test role credentials never enter frontend tests.

Each job writes a concise outcome to the Actions summary. Investigate the first
failed step, its test name/report, and the policy decision JSON. Missing evidence
is a failure, never a green placeholder. Keep private diagnostics private; do not
upload environment files or raw database logs. No continue-on-error masks a required
failure. The existing upstream TestClient HTTPX deprecation warning is documented
and does not change test outcomes.

Compose uses random disposable project names and verifies ownership labels before
normal/fallback cleanup. Cancellation cleanup is best effort; a hard runner kill
can prevent final steps, and hosted runners are disposable. No global Docker prune
or existing developer/coursework volume cleanup is authorized.

## Ruleset rollout after separate approval

The observed active main ruleset requires PRs, zero external approvals, no force
push/deletion and no bypass actors. Its required-check list was empty at planning
review. Classic branch-protection 404 does not mean no ruleset exists.

After the seven real contexts succeed, obtain owner approval to add all seven,
bind the source to GitHub Actions (observed app ID 15368), require current branches
and resolved conversations, and preserve zero external approvals and no bypass.
Do not demand impossible self-approval. Verify effective rules through the ruleset
and branch-rules APIs, then use a controlled PR to inspect missing/failing-check
blocking. Never test by attempting an unauthorized push or merge to main.
Until this is configured and verified, these are CI checks, not verified remote
merge-blocking requirements. Passing checks never grant permission to merge.

## P1-05 audit remediation

The initial hosted checks passed but uploaded zero artifacts: upload-artifact's
hidden-file default excluded .artifacts. The follow-up explicitly enables hidden
files only for the reviewed generated-report paths and sets missing-file behavior
to error. JUnit validation/sanitization still precedes uploads; browser artifacts
contain synthetic UI data only. Retention remains seven days for browser reports
and fourteen for JUnit/security reports. A green local run does not verify hosted
retention: inspect the run's artifact API/list and download the archives.

The workflow policy now compares parsed command sequences by workflow, job and
named step against reviewed contracts. Missing steps, no-op replacements, appended
shell bypasses, shell/directory/environment overrides and missing/altered uploads
fail validation. Frontend script contracts prevent npm indirection becoming a
no-op. Contracts need an explicit reviewed update when legitimate commands change.
This is a change-detection control, not a shell interpreter or independent trust
root: an author can edit both policy and implementation, so owner review is required.

Trivy 0.76.0 container reports must identify the scanned immutable image, OS,
recent timestamp, result types and nonempty package inventory. Every vulnerability
must map to its inventory package; duplicate packages/findings fail. Full inventory
counts and fingerprints in .github/security-inventory.json derive from the original
reports whose hashes are in the unchanged approved baseline. Missing/truncated or
changed inventories fail. Debian package IDs retain epoch/revision even when the
upstream Version field differs; language packages use their name/version identity.
HIGH/CRITICAL occurrence counts and identities must exactly equal the approved
baseline; even removals require evidence review rather than silently passing an
ambiguous incomplete scan. This stricter validation does not broaden acceptance.
Reports remain scanner evidence, not proof that every vulnerability is exploitable.

The daily monitor records safe outcome codes after each stage. Python audit, npm
audit, each registry lookup, each image build/identity and image scanning continue
independently after bounded failures. Failed builds never reuse stale local images.
Image scanning attempts every role and retains successful reports when another
role fails. Any required failure makes the overall result fail. Status summaries
contain no raw exception text or credential dumps. A hard job cancellation/timeout
can still interrupt execution; retained partial evidence is not a completed daily
review. The owner must inspect failed/missing daily runs and review CRITICAL risk.

P1-05 completion remains subject to verified hosted artifacts, passing checks and
owner review. No ruleset change, merge, production clearance or P1-06 is implied.
