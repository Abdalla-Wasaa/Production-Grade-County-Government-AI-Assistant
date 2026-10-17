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

P1-06 documentation and acceptance verification is authorized on
`docs/p1-06-foundation-acceptance`. Reopen/correct issue #7 without erasing its
criteria/history; reconcile docs; verify a clean exact-commit checkout; push and
open one focused review PR. If genuine Docker isolation is unavailable, stop the
affected replay and mark its criteria pending. Never invent human review or approval.
Do not change application code without separate approval for a verified defect.
Do not change rulesets, vulnerability baseline/acceptance or its expiry. Synthetic
local development only. No merge, deployment, coursework changes or Phase 2 work.
