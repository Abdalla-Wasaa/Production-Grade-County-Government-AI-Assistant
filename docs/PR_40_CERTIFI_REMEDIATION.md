# PR #40 certifi remediation and runtime checkpoint

Status: targeted lockfile correction prepared; changed application execution and
security-record updates remain unapproved. No push or hosted rerun yet.

## Confirmed cause and selected release

Hosted job 118851476145 in run 39487455472 reported certifi 2026.7.22 affected by
GHSA-6q48-6c7w-9gw2 in both backend and tooling audit artifacts. It was a real audit
failure, not missing evidence or an ignored check. The
[maintainer advisory](https://github.com/certifi/python-certifi/security/advisories/GHSA-6q48-6c7w-9gw2)
confirms compromised emSign intermediate CA keys and root removal, with potential
on-path TLS interception. The upstream advisory marks the issue CRITICAL and names
2026.10.18 as patched. The
[reviewed advisory database](https://github.com/advisories/GHSA-6q48-6c7w-9gw2)
and hosted audit recommend 2026.10.19, which restores unaffected roots.
This corrects the previous publication-time inability to retrieve the advisory page.
No exploit against this application has been reproduced.

Selected release: **2026.10.19**. [PyPI release metadata](https://pypi.org/pypi/certifi/2026.10.19/json)
confirms it is non-yanked, requires Python >=3.7 and has a universal Python wheel.
Both wheel and sdist bytes were downloaded independently and SHA-256 verified against
PyPI metadata and the updated lock entries. No CA-verification bypass is introduced.

## Affected environments and minimal change

Certifi is not a direct project dependency. HTTPX 0.28.1 and httpcore 1.0.9 depend
on it in backend/uv.lock, covering development/test environments and the packaged
backend runtime. CI tooling receives it through Requests 2.34.2 (pip-audit and its
supporting tooling dependencies) in requirements-ci.lock. requirements-dev.txt lists
tooling roots, not this transitive package; backend/pyproject.toml declares HTTPX,
not certifi. Neither root declaration needs a new unrelated direct dependency.
Frontend npm packages are unaffected. Existing installed backend environments and
images remain old until a later authorized locked sync/rebuild; editing locks alone
does not retrofit them. A separate temporary audit-tool environment was created
from the updated hash-locked tooling requirements, without importing application code.

Only backend/uv.lock and requirements-ci.lock change package pins, artifact URLs,
versions and hashes. Targeted `uv lock --upgrade-package certifi==2026.10.19` changed
exactly certifi; all other backend package names/versions remain identical. Tooling
lock edits likewise change only certifi and its wheel/sdist hashes. No model weights,
benchmark/evaluation evidence, sampling, source interface, network rules or privileges
are changed. No new dependencies are introduced.

## Validation permitted before changed-app runtime approval

- `uv lock --project backend --check` passed; locked resolution is consistent.
- Existing scripts/audit_python.py ran against both updated exact dependency sets:
  backend 45 packages, tooling 34 packages, zero advisories. No ignored findings.
- PyPI wheel SHA-256: 42d35340cc5b9ba78e818ddbff0c5b1c2b779de448a340fd1b989f5fa8670e1b.
- PyPI sdist SHA-256: 035c1e85572b141bf1c3a3eff0e33a8eb74917522f2559075ff8d2fea780a1ae.
- Packaging-only runtime build succeeded; no image application process was run.
- Trivy 0.76.0 reports 44 HIGH/0 CRITICAL, zero fixable HIGH/CRITICAL, exact unchanged
  backend finding rows and no matches in freshly retrieved KEV evidence. Python
  advisory audit and image scanner are complementary, not interchangeable.
- Repository formatting/documentation and secret checks are performed for this commit.
  Application regressions are NOT rerun before owner runtime approval. Prior 336-pass
  results and six-passing/one-failing hosted results belong to the previous PR head.

Image ID: `sha256:1752d1f6bdda54dc8be85d864fd6a132a43642e9ecc74c25ff79acfe1a208148`.
Complete backend inventory retains 122 packages; only certifi version changes.
Old inventory SHA-256: `3b313e4e52f23217faa9d0af79c3e339d2c4477aba1e6d66146dc1457c844aae`.
New inventory SHA-256: `f508af45849f6d64bbf4f6cc65b4cd411e22da300492f630f479cc64f1be3de4`.
Database/web images are unchanged and not rescanned here; previous hosted evidence
retains 71 HIGH/3 CRITICAL and zero respectively, for 115 HIGH/3 CRITICAL inherited
occurrences overall. No finding is suppressed or automatically accepted.
Raw local evidence: /tmp/county-certifi-remediation-audit, its sibling audit log,
/tmp/county-certifi-remediation-image.json, /tmp/county-certifi-remediation-kev.json
and /tmp/county-certifi-remediation-security-summary.json.

## Exact authorization boundary

Old accepted exposure:
`d015b5cadfa07781d0f2eb063bb11bbd7dea923a684bad94a78dbae3506f476d`.
New prepared exposure:
`8fb62f79a81d7d1216126f0b4ff40fb38a9e3d01b625646b121bcb83e5b00c9f`.
The lockfile is part of the application exposure. Normal policy correctly rejects
the new hash; the complete backend inventory also differs. Prior approval cannot
be reused merely because this is a security improvement. The trust-store change
reduces known TLS risk but alters runtime dependencies and must be tested normally.

Required next owner decision: authorize isolated synthetic, mocked-network execution
at the final remediation commit and new exposure for the 336 backend/provider/
orchestration/sampling regressions and applicable static/security checks. No live
inference, new models, production, real data or public service is requested.

After passing validation, separately review the minimum security-record update:
backend scan provenance in .github/security-baseline.json (no finding-row changes),
backend inventory reference in .github/security-inventory.json, exact active decision
in .github/security-risk-acceptances.json, byte-preserved prior policy snapshot,
this assessment, docs/SECURITY.md and AGENTS.md. Do not modify these records now.
Publication to PR #40 follows the required exact-exposure/inventory decision and
normal seven checks, not a bypass of policy or automatic acceptance.

The existing expiry remains 23 October 2026, 23:59 EAT. Actual 20 October human
CRITICAL review is historical, not a future review. No acceptance extension or
invented human confirmation. Historical records and all seven checks/branch rules
remain unchanged. No automatic merge or P3-04 readiness approval.
