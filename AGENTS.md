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
On 17 October 2026 the owner separately approved the exact tested P2-02 source
2a3339410aba6c3037ef349569afffbbae002bd4, exposure
0b8f2dc7e55e72fbc96325edbec4d57a5a97c9eb52d4fae3251e9aec302b958d,
unchanged inventories and 115 HIGH/3 CRITICAL inherited findings. Only the five
specified security/documentation files may change for this acceptance update.
The previous P2-01 acceptance is preserved byte-for-byte in its historical snapshot.
Acceptance is isolated synthetic local development only; expiry remains
23 October 2026 at 23:59 EAT. Daily human CRITICAL reviews and all existing
invalidation triggers remain mandatory; no automatic future-exposure approval,
renewal or scope expansion. No real citizen/county data, production credentials,
public/production deployment, automatic merge or next milestone.
Run normal checks and verify all seven hosted contexts on PR #25 after pushing;
fix only genuine remaining defects without weakening controls. Keep scans, baseline,
inventories, policies, workflows, ruleset and normal PR review unchanged. A further
exposure change requires a new exact owner decision, not a silently updated hash.
Coursework outside this official repository remains strictly read-only.
