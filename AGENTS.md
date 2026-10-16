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

P1-02 PostgreSQL/Alembic foundation is authorized on
`build/p1-02-postgresql-alembic`: Python 3.12, PostgreSQL 17, SQLAlchemy 2.x,
async Psycopg 3, explicit Alembic baseline, readiness, tests, documentation and CI.
Keep liveness independent of the database. No domain tables or automatic migrations.
Develop only a fictional county environment with synthetic information. English
and Kiswahili remain required. Real-pilot decisions stay behind the pre-pilot gate.
No real citizen records, county credentials, confidential documents, payments,
public deployment or live county integration are authorized.
Use dedicated branches, Conventional Commits, meaningful tests, green relevant CI,
and PRs reviewed by the sole maintainer. Pushing this branch and opening its PR are
authorized. Do not merge, deploy, release, start P1-03, or add auth/chat/AI features.
