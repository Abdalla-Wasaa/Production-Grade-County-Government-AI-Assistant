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

P1-04 security follow-up is authorized on
`fix/p1-04-container-security-review`, starting from reviewed main after PR #11.
The owner approved carrying the tested backend Trixie image remediation and dated
vulnerability register into a dedicated follow-up branch and PR. Preserve all
existing security controls, scan thresholds, dependency locks and checks. Only
synthetic local development is authorized. Do not modify coursework or its Docker
resources. Push and open the follow-up PR for owner review; do not merge, deploy,
release, begin P1-05, change PostgreSQL distro/storage, or add application features.
