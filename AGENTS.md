# Persistent engineering rules

- Use professional modular architecture with clear responsibilities and boundaries.
- Follow Conventional Commits for all commits.
- Work through feature branches and pull requests.
- Never commit directly to `main` after the initial repository initialization commit.
- Never expose secrets or credentials in source code, commits, logs, or documentation.
- Never modify existing AIEngineeringClass coursework. Treat coursework outside this
  official repository as read-only reference material; authorized work within this
  repository is permitted even though it is located inside the coursework directory.
- Add tests for implementation changes and run the relevant checks before review.
- Explain important design decisions and their tradeoffs in reviewable documentation
  or pull request descriptions.
- Require the user's explicit approval before merging or beginning another phase.

## Current scope

The owner authorizes issue #19 P2-03 on feat/p2-03-conversation-persistence from
merged PR #25 (main 5ff0e2281ed7f4984ffcb090a3c87c14157fd800). Implement the
explicitly approved persistence contract amendment, private conversation CRUD and
user-only message storage/history, migrations and tests. No assistant placeholders,
LLM calls, RAG, frontend history or unrelated work.

Before executing changed app code, stop with exact commit, exposure hash, dependency
delta and vulnerability evidence for a separate owner synthetic-runtime decision.
Do not dispatch changed-runtime hosted CI or reuse/modify the P2-02 acceptance.
Preserve all seven checks, scans, policy records, inventories and branch protection.
Expiry remains 23 October 2026, 23:59 EAT; daily actual human CRITICAL review and
all invalidation triggers remain required. No real data or production deployment.
No PR until authorized, no automatic merge. Coursework remains read-only.

On 18 October the owner explicitly authorized isolated backend/PostgreSQL validation
of 0dd84f9658c1c8dae4beee9a1fac4214658b4088, exposure
f0fa257c41dc225ba807ffd87aba15897fc1f77bde82323d56ed6782b6fe32b3.
All 25 unit/contract and 20 real-PG cases passed without source corrections.
At that checkpoint web/Compose execution and the slim-base patch were pending;
the owner subsequently explicitly authorized that pinned Dockerfile remediation
and controlled synthetic web/Compose validation. That validation is complete.
Exposure is now 88669fbe4cfafc7dc45e6775546e44e6ca8bcbec1dcacfb0f89a36c702af19b4.
The 51-case PostgreSQL result, actual Nginx/browser/auth/recovery/persistence checks
and isolated cleanup are recorded in docs/P2_03_EXPOSURE_ASSESSMENT.md. Narrow
test corrections fixed duplicate module names, the bounded suite subprocess budget
and the exact approved OpenAPI path expectation; no application checks were weakened.
Security-record updates, push, PR and merge remain unapproved. No daily human
CRITICAL review is asserted; actual confirmation remains required. Stop for the
consolidated seven-file record decision; do not extend expiry or auto-accept exposure.

## Owner-approved P2-03 records, 18 October 2026

The owner explicitly approved the seven-file update for f9520eb932341a150f26ea1d977b8fff67a51c7d,
exposure 88669fbe4cfafc7dc45e6775546e44e6ca8bcbec1dcacfb0f89a36c702af19b4,
web inventory 21 packages and unchanged 115 HIGH/3 CRITICAL inherited occurrences.
Previous P2-02 policy bytes are preserved in docs/security/p2-03/p2-02-policy-snapshot.json.
Expiry remains 23 October 2026, 23:59 EAT. Synthetic isolated local development only;
no real data or production deployment. All invalidation triggers, seven checks, scans,
branch protection and owner PR review remain mandatory. Push and PR linked to issue
19 are now authorized; no merge. Human CRITICAL review for today remains pending: no
review completion is asserted. Automated policy does not require a human-review
timestamp before CI; documented human acceptance obligations remain incomplete even
if CI passes. This approval does not grant unconditional milestone acceptance.
