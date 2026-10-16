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

P1-04 secure local Docker Compose environment is authorized on
`build/p1-04-compose-environment`: non-root locked application images, isolated
web/backend/PostgreSQL networks, synthetic per-role secrets, explicit migrations,
guarded disposable-resource reset, tests, CI and documentation. Reopening issue
#5, pushing this branch and creating its review PR are authorized. Preserve all
existing backend, frontend, documentation and security checks. Only synthetic
information is authorized. Do not modify coursework containers or storage.
Do not merge, deploy, release, begin P1-05, or add authentication, chat, AI
providers, RAG, tools, agents or application domain tables.
