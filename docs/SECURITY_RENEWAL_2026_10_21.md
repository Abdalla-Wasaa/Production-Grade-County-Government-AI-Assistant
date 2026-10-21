# Owner-approved restricted-development renewal — 21 October 2026

Owner approved the exact five-file renewal and explicitly confirmed actual CRITICAL
review on 21 October. This PR records the decision; renewal becomes effective only
after required approval, merge and repository-policy conditions. Until then main
still expires on 23 October 2026 at 23:59 EAT. No automatic merge.

Merged PR #42: `2fc0ecfd895739eef3f026c2961c286c0a1397a8`.
Exact exposure: `015755bffa0f038986d719624979b317cb5e5527dceed76447fd207d09747ab1`.
Proposed end: **30 October 2026, 23:59 EAT** (`2026-10-30T20:59:00+00:00`).
The approved_at value records processing of the actual owner decision; it does not
claim the minute the personal review was performed.
The proposed interval is less than the existing 30-day policy maximum.

## Fresh packaging-only evidence

No application execution, model inference, image change or accepted-record edit.
Trivy 0.76.0 current database updated 21 October 2026 07:13:45 UTC. Fresh image
scans retain full findings and packages, with no configuration/ignore overrides.
Fresh CISA retrieval returns catalogue 2026.10.20; no reviewed HIGH/CRITICAL match.
Absence from KEV does not establish no exploitation. Raw reports, immutable input,
DB refresh log and assessment are retained in the private post-42-renewal handoff.

| Image | HIGH | CRITICAL | Fixable HIGH/CRITICAL | Packages | Inventory SHA-256 |
| --- | ---: | ---: | ---: | ---: | --- |
| builder | 56 | 1 | 0 | 496 | `f779da813c7aed7ffec7866cc9d7d9c8c8db887122418b0ca281125a8005da35` |
| web | 0 | 0 | 0 | 21 | `e9d19af8839b51cd311f6b527994b6cc624ee2b0491513c293f6fefa6cb60443` |
| backend | 44 | 0 | 0 | 122 | `f508af45849f6d64bbf4f6cc65b4cd411e22da300492f630f479cc64f1be3de4` |
| db | 71 | 3 | 0 | 144 | `f0ff6951e8f3157a9f0e6d15387c68b6e4e591afd21d2d0da972c122ed1ad288` |

All finding rows (versions, severity, fix/status), duplicate multiplicities and
complete inventories match reviewed references. No newly fixable finding, severity
increase or new KEV match was found. No blanket acceptance of unchanged findings:
owner must review each bound runtime and builder occurrence before approval.
Runtime findings are individually recorded in `.github/security-baseline.json`;
builder findings in `docs/security/p3-03d/actual-validation.json`. Summed image
occurrences are 171 HIGH/4 CRITICAL, including duplicates across images; they are
not 175 distinct CVEs. Runtime inventory/baseline files need no changes.

## Immutable references and fresh report identities

```json
{
  "image_ids": {
    "builder": "sha256:8a7503b7c29922106dd6f186970fc3197ff6f5ace643345762efa9b598f14348",
    "web": "sha256:9ba8a76aed3f8b9179f15781f1ab21f68d4e46c0508d749502e39b3b61276e1e",
    "backend": "sha256:802a3a749442ebec041ba3a3a40c61bc4b6dadd3b89cf268c0c90b8d1581927a",
    "db": "sha256:b29824152e3c5ca40e34b13cf4f532403a70805aa3717f71bd6b1051d5e6fb35"
  },
  "runtime_base_pins": {
    "web": "sha256:4ac59c85c8c46d9e91eaabd2122cda4923ba380cf11f4138e389f069bcdc77a3",
    "backend": "sha256:a6e34c598f2467ed0e9a8d349809fcd8b5c603269512df273a0bb1784edc11b1",
    "db": "sha256:3645570cccdfa447589da9f57dd740faa29b30938e861289a5574b6ca6b03826"
  },
  "node_base_pin": "sha256:91acba91b842bec0bf7ea6f5e09c644c7ccad72c4996ed9616d861d1c7cd60d4",
  "npm_version": "11.21.1",
  "npm_archive_sha256": "dd77c48eb845f4856c2cdba347cfb52bd877a2655a1ea48ff0c4796e3df9dd7b",
  "fresh_report_hashes": {
    "builder": "b8f6503c8cf1ebb9eb2c8ea92df51ef170c7cc5dd7982f4c59682ac769c301c4",
    "web": "6835224e1a7ca21b7e3138256b64fd88aa82c42370472026d85ccb5651b15d2f",
    "backend": "e089b3c3e0a317fafe30bf0a34ea0b8833af44244d8718d8419392565bcc0626",
    "db": "707225f5073ab1a8300d1c69009a232d111d7c7ab7a4175eba103e43fad32061"
  }
}
```

Version execution evidence from authorized P3-03D validation confirms Node 24.22.0,
npm 11.21.1, builder UID 1000 and web UID/GID 101:101. Source/exposure matches the
merged baseline; fresh work here is non-executing analysis. Existing Compose proof
covers internal application/database networks, loopback web binding, no DB/backend
host ports, dropped capabilities, read-only roots, secret files and least-privilege
DB roles. No infrastructure or permissions have changed; controls mitigate rather
than eliminate compromise or build supply-chain risk.

## Actual human CRITICAL review — confirmed for 21 October

The owner explicitly replied: “I personally completed this review on 21 October
and acknowledge the residual risks”. This confirms the three unique CVEs including
both zlib occurrences. The 20 October record remains historical; future daily
reviews still require actual confirmation.
Confirmation recorded at 2026-10-21T15:07:08.002119+00:00.
The four scanner occurrences represent three unique CVEs:

| CVE | Image/package/version | Prerequisite, exposure and residual assessment |
| --- | --- | --- |
| CVE-2025-7458 | PostgreSQL / libsqlite3-0 3.40.1-2+deb12u2 | Crafted SQLite SQL with large ORDER BY input; no demonstrated current API exploit, but installed vulnerable library remains. Internal DB/no host ports, parameterized application SQL and least privilege reduce access. Current Bookworm scanner has no fixed package; newer SQLite/upstream and other suites contain fixes. |
| CVE-2026-6653 | PostgreSQL / libxml2 2.9.14+dfsg-1.3~deb12u6 | Authenticated PostgreSQL SQL/XML remains an assessed plausible path; no reproduced application exploit. Internal DB and least-privilege SQL mitigate; do not call it unreachable. Scanner fix_deferred, no reported current-package fix. Vendor tracker refresh timed out in this investigation; fresh scanner/KEV evidence is available, and the prior exposure assessment is retained. |
| CVE-2023-45853 | PostgreSQL / zlib1g 1:1.2.13.dfsg-1 | Crafted inputs to affected MiniZip routines; Debian says contrib/minizip is not built into these Bookworm binaries. Retain CRITICAL scanner occurrence/will_not_fix rather than suppress it. No demonstrated current exploitable route; package applicability qualification is not a blanket zlib safety claim. |
| CVE-2023-45853 | Node builder / same zlib1g version | Same MiniZip applicability qualification, separately counted image occurrence. Builder handles source/dependency inputs and produces assets; build-only is not risk-free. Checksum-pinned npm, lockfile installs, non-root project builds and isolated ephemeral workloads mitigate supply-chain exposure. |

No fix is reported for the installed package versions; that does not mean no fix
exists globally or in a different supported distribution. All current severities
remain CRITICAL; none matches the retrieved KEV catalogue. No independently
confirmed exploitation of this application is established. The owner must assess
residual risk rather than infer safety from counts or uncertainty.

Vendor references:
- https://security-tracker.debian.org/tracker/CVE-2025-7458
- https://security-tracker.debian.org/tracker/CVE-2026-6653
- https://security-tracker.debian.org/tracker/CVE-2023-45853

## Tag drift and remaining limits

21 October four-tag investigation is preserved. Node's vendor digest and complete
npm patch now remove its identified fixable builder findings. Nginx/Python/PG
upstream tag movement did not demonstrate a reduction in relevant HIGH/CRITICAL
rows; their immutable deployed pins remain unchanged. PostgreSQL vendor gosu
findings do not reappear: the project runtime removes gosu. Keep tag alerts active;
review subsequent drift/fixes immediately instead of silently updating pins.
Unchanged reports do not authorize automatic future acceptance.

## Proposed controls and permitted work

Isolated synthetic local builds, deterministic/mocked tests, maintenance, evidence
and independent human review only. New application exposure, changed privileges,
networking or live inference needs its own reviewed authorization; renewal alone
is not a performance-diagnostic/inference grant. Keep Ollama loopback-only and do
not run models as part of this renewal. No real citizen/county data, production
credentials, public endpoints, deployment or P3-04 approval. No new models.

Require actual daily human review of every CRITICAL assessment, daily automated
scans/monitoring and visible investigation of failures. Immediately invalidate the
appropriate acceptance on a fix becoming available, new/escalated/known-exploited
finding, changed exposure/inventory/dependencies or isolation/privilege change.
Stop affected work at expiry without a new explicit decision; no grace period or
automatic renewal. Preserve all seven app-bound checks and strict protected PRs.

## Exact five-file proposal and history

Only active risk acceptance, this decision document, SECURITY.md, AGENTS.md and
`docs/security/renewal-2026-10-21/p3-03d-acceptance-snapshot.json` change. The snapshot
preserves the previous active approval byte-for-byte (SHA-256 `b1f3b20ccdf3eeb1e2906400fff4568ac511887df2705422d0ce31254ad9d526`).
Baseline/inventory policy, prior snapshots and all other historical records stay
unchanged. The pending timestamp was completed only after actual owner review confirmation
satisfied the previously explicit conditional approval. No review was invented or
backdated. Effective renewal requires merge and normal repository-policy checks.

Issue #39 remains open: 96 independent bilingual assessments, quality gates,
latency and eight-call cold/resident diagnostic are outstanding. Renewal cannot
substitute for those criteria or establish model readiness.

## Final merged-main CI verification

All seven required contexts completed successfully on merged main commit
2fc0ecfd895739eef3f026c2961c286c0a1397a8, bound to GitHub Actions app 15368.
Compose briefly remained in progress after all steps succeeded; GitHub finalized
it successfully without rerunning tests, changing code or manufacturing status.
Fresh evidence is in merged-main-checks.json in the owner-controlled handoff.
