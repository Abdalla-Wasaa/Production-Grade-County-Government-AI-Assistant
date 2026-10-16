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

P1-05 quality/security CI implementation is authorized on `ci/p1-05-quality-gates`.
Reopen/correct issue #6, implement the approved gates, push and open a review PR.
Preserve all existing tests and security controls. Risk decisions require explicit
owner approval; never auto-accept or renew findings. Synthetic development only.
Do not change GitHub settings, PostgreSQL distro/storage, coursework or unrelated
application behavior. Do not merge, deploy or begin P1-06.
