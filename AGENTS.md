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

Issue #18, P2-02 frontend authentication, is authorized from merged backend PR #24
(main ecc9f76). Use feat/p2-02-frontend-authentication. Implement bilingual
login/activation, memory-only session state, protected account routes, serialized
refresh/restoration, logout and own-session management with meaningful tests.
No public registration, admin dashboard, conversations, AI/RAG or deployment.
Prepare source, static/build/audit and complete image scan evidence, then stop at
the exact human changed-exposure decision before running changed-app tests/Compose
or opening runtime CI. The P2-01 acceptance does not cover changed frontend code.
Do not change baseline/inventory/acceptance records, expiry, CI policies, workflows
or rulesets without explicit authorization. Preserve all seven checks and normal PR
review. Existing expiry remains 23 October 2026 at 23:59 EAT; daily human CRITICAL
reviews remain mandatory and must not be fabricated. Synthetic isolated local
information only; no real citizen/county data, production credentials or public/
production deployment. No automatic merge or start of another milestone.
Coursework outside this official repository remains strictly read-only.
