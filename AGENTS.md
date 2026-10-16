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

Phase 0 architecture documentation is complete. The current authorized follow-up
adds repository workflow documentation, GitHub templates, and checks that run on
this documentation/tooling-only repository. Remain on `docs/phase-0-architecture`.
Do not implement application functionality, modify coursework, push, create a PR,
merge, release, or begin another phase without the user's explicit authorization.
