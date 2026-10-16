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

P1-01 backend foundation is authorized on `build/p1-01-backend-foundation`:
Python 3.12, uv with committed lockfile, FastAPI/Pydantic v2 settings/lifecycle,
liveness, safe HTTP/logging boundaries, tests, documentation and relevant CI.
Develop only a fictional county environment with synthetic information. English
and Kiswahili remain required. Real-pilot decisions are deferred to the documented
pre-pilot gate. No real citizen records, county credentials, confidential documents,
payments, public deployment, or live county integration are authorized.
All implementation uses dedicated feature branches, Conventional Commits, meaningful
tests, green relevant GitHub Actions checks, and PRs reviewed by the sole maintainer.
The user authorized pushing this feature branch and opening its PR into main.
Do not merge, deploy, release, start P1-02, or add auth/database/chat/AI functionality.
