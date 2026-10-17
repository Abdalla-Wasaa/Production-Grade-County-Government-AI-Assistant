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
On 17 October 2026 the owner explicitly authorized isolated synthetic frontend,
browser/accessibility and backend integration validation of source 17f03c0 and
reviewed exposure c65d01bdd17de179fce4284328d372aeb23b17b7b49b10e0cd09688c919a6b28,
including bounded test-driven corrections within issue #18 with no new dependencies.
This authorizes validation only, not acceptance-record changes or automatic reuse
of P2-01 acceptance. Recheck exposure/security delta after corrections; present the
exact final security decision before opening the frontend PR. No merge is approved.
Do not change baseline/inventory/acceptance records, expiry, CI policies, workflows
or rulesets without explicit authorization. Preserve all seven checks and normal PR
review. Existing expiry remains 23 October 2026 at 23:59 EAT; daily human CRITICAL
reviews remain mandatory and must not be fabricated. Synthetic isolated local
information only; no real citizen/county data, production credentials or public/
production deployment. No automatic merge or start of another milestone.
Coursework outside this official repository remains strictly read-only.
