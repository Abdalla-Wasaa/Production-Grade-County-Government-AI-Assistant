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

P1-03 React frontend foundation is authorized on
`build/p1-03-react-frontend-foundation`: isolated Node 24, React/Vite/strict
TypeScript/Tailwind 4/React Router, npm exact pins and lockfile, bilingual shell,
accessibility, tests, documentation and CI. Keep the shell independent of backend
availability. Development Kiswahili copy is permitted, explicitly pending human
review before any pilot. No external translation API or official approval claims.
Only fictional/synthetic information is authorized; no real citizen records,
credentials, confidential documents, payments, official branding or live systems.
Use dedicated branches, Conventional Commits, meaningful tests, green relevant CI
and a PR reviewed by the sole maintainer. Reopening/correcting issue #4, pushing
this branch and opening its PR are authorized. Preserve existing backend checks.
Do not merge, deploy, release, start P1-04, or add auth/chat/provider/RAG/tools.
