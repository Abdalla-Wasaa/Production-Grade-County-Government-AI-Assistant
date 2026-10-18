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
