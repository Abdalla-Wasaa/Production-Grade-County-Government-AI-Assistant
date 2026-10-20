# P3-03B scoped exposure assessment

Owner-authorized tested source: `9594dc339bd93939113817a6ba0a132ecc062ea3`.
Exposure: `d015b5cadfa07781d0f2eb063bb11bbd7dea923a684bad94a78dbae3506f476d`.

The sampling correction replaces per-model implicit defaults with validated common
settings: temperature 0.7, top_p 0.8, top_k 20, min_p 0, repeat_penalty 1 and seed 42.
Existing interface, allowlist, prompt orchestration, cancellation, timeouts and logs
are preserved. P3-03A did not cover changed source hash or Qwen benchmark configuration.
No new endpoints, external inference access, privileges, credentials or data storage.
Sampling changes output behavior and cannot establish factual safety. Model weights
are additional supply-chain/behavioral inputs; verified hashes do not certify quality.

[Validation](P3_03B_VALIDATION_REPORT.md): 336 passed; static and secret checks passed.
Changed backend scan 20 October 21:33 EAT: 44 HIGH, no CRITICAL, no reported fixes or
KEV matches; exact inventory and finding rows unchanged. Reused unchanged database/web
scans from 20 October 16:36 UTC: 71 HIGH/3 CRITICAL and zero respectively. Total 115
HIGH/3 CRITICAL. This is scanner evidence, not proof of absence of exploitability.
Three inherited PostgreSQL CRITICAL findings remain SQLite CVE-2025-7458 (crafted
SQLite SQL prerequisite, no demonstrated current API exploit), libxml2 CVE-2026-6653
(authenticated SQL/XML is a plausible compromise path, no reproduced exploit), and
zlib1g CVE-2023-45853 (Debian excludes vulnerable MiniZip code from these binaries;
scanner occurrence retained). Compensating controls: synthetic local data, DB least
privilege, no arbitrary SQL/XML API, loopback-only offline inference, redaction,
full scanning, seven CI checks, protected PR workflow and actual daily human review.

Owner explicitly confirmed actual 20 October review earlier; this decision does not
invent another review or future-day review. Expiry is unchanged at 23 October 2026,
23:59 EAT. Fix/new-finding/severity/KEV/exposure/dependency invalidation rules remain.
Production, public deployment and real citizen data remain prohibited.

The owner authorized the minimum scoped record update in the current request.
AGENTS requires separate runtime and record decisions, both explicitly provided;
it does not impose a new exact-diff review for this milestone. Prior milestone
exact-diff statements are historical and scoped to those approvals.
Previous active approval is preserved byte-for-byte in
[historical snapshot](security/p3-03b/p3-03a-acceptance-snapshot.json).
Snapshot SHA-256: `9619c830542bb5495256e338b8c57d82ef5536b2d8bf6a3bba81928952545211`.
Only this assessment, active acceptance, historical snapshot, SECURITY and AGENTS
are changed for the decision. Baseline/inventory/CI/privileges remain unchanged.

Benchmark prerequisites remain conditional: matching accepted exposure, both verified
manifests, current human review/expiry, loopback/no external inference route,
5 GiB combined cgroup RAM ceiling and 512 MiB swap ceiling, adequate host headroom.
One model/request at a time; stop on OOM/thrashing or inability to enforce limits.
CPU-only hardware and substantial existing swap may prevent the 15-second p95 gate.
No resource/timeout relaxation to force a pass.

Only approved cached llama3.2:3b and qwen3:4b-instruct-2507-q4_K_M may run, at most
96 scored plus six warm-ups, identical frozen prompts/parameters/30-second deadline.
No further models, downloads, weight changes, cloud services or application edits.
Policy abstentions remain separate. Independent bilingual review and reviewed holdout
remain outstanding; no automatic selection or P3-04 readiness follows this acceptance.
