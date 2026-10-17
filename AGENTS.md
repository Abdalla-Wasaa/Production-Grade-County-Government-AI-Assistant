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

Phase 1 is technically closed for restricted synthetic development. P2-01 backend
implementation is authorized subject to reviewed, merged contracts. Contract PR #23 is merged. Use feat/p2-01-account-authentication from those contracts;
the owner now authorizes isolated synthetic backend/PostgreSQL/Compose validation,
benchmarking and bounded P2-01 corrections within the seven approved dependencies.
The implementation PR may be opened for review under the original workflow request;
its security checks must remain failing until an explicitly authorized policy-record
decision resolves changed exposure/inventory. No acceptance/hash/inventory file edits
or expiry extension are authorized by validation permission.
Fixed citizen/staff/admin roles; invite-only activation and operator-assisted recovery;
no frontend auth, conversations, live email, AI/RAG/tools or deployment in P2-01.
Never silently reuse/update the Phase 1 exposure-bound vulnerability acceptance,
change its hash, expand scope or extend expiry. Changed application execution under
an exception requires focused assessment/scans and the policy-required owner decision.
Preserve all seven checks and branch rules; mark blocked verification pending.
Coursework remains read-only. No automatic merge or start of a later milestone.
