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

P2-01 backend implementation and isolated synthetic validation are authorized under
merged contract PR #23. Work on feat/p2-01-account-authentication and PR #24.
On 17 October 2026 the owner separately approved the exact implementation at
933967ea2a03368677e175f65f6f65dc193a8716, exposure
d82e1a0e6a43f2bea054684dd7e5fad9a2e2fbb96723a93e74f0bde1bf7bfb17
and backend inventory
7c9d236e62e9b96b9dfe7ca03dd92b1d999c6bacfb7fb8f67949a9790d88274e.
Only the seven proposed security/documentation files may change for this approval;
the original Phase 1 records are preserved as an unchanged historical snapshot.
The separate P2-01 acceptance covers only the exact 118 inherited occurrences,
reviewed exposure and seven added dependencies, for isolated synthetic development.
Expiry remains 23 October 2026 at 23:59 EAT. Daily human CRITICAL reviews and all
existing invalidation triggers remain required; no automatic approval of later
exposure changes, acceptance expansion or renewal. Production/public deployment,
real citizen/county data and production credentials remain prohibited.
Run normal repository/Compose validation and all seven hosted checks; do not bypass
rules or manufacture reports. Preserve scans, branch protection and PR review.
Fixed citizen/staff/admin roles; invite-only activation and operator-assisted recovery;
no frontend auth, conversations, live email, AI/RAG/tools or deployment in P2-01.
Coursework remains read-only. No automatic merge or start of a later milestone.
