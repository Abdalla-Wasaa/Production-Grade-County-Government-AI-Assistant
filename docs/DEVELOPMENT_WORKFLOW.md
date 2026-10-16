# Development workflow

The official checkout has its own Git repository even though it is nested beneath
the AIEngineeringClass coursework directory. Coursework is read-only; never run its
scripts, install into its environments or alter its Docker resources.

## Issue, branch, implementation and review

Read AGENTS.md and the approved issue/docs. Confirm root, official origin, branch,
clean working tree and current main using git pull --ff-only before branching.
Use dedicated feature branches, Conventional Commits, focused diffs and meaningful
tests. Stage explicit project paths, inspect the staged diff and scan for secrets.
Do not rewrite published history, force-push or commit implementation to main.

P1-05 is authorized on ci/p1-05-quality-gates. Issue #6 was reopened to correct its
premature closure. Phase 0 through P1-04 and security PR #12 are merged. An issue
checkbox or prior merge is not approval to begin another milestone. Preserve the
modular monolith and synthetic-only scope. No authentication/chat/AI/RAG/tools,
public deployment or real county integration is introduced here.

Open a PR only when authorized. Include actual results, design decisions, failures,
residual risks and applicable docs. Resolve review blockers and await explicit owner
approval before merging. The sole maintainer reviews; do not manufacture independent
self-approval or require an unavailable external reviewer. Do not start P1-06.

## Checks and failure investigation

[CI architecture](CI.md) defines the seven stable contexts, deterministic installs,
local commands, reports, policy tests, vulnerability decisions, scheduled monitoring
and the separately approved ruleset rollout. [CONTRIBUTING.md](../CONTRIBUTING.md)
has development checks. [Compose operations](COMPOSE_DEVELOPMENT.md) explains scoped
setup, explicit migrations, persistence and guarded reset.

All PRs run full relevant checks; main pushes and manual dispatch support verification.
A green result is not a security waiver, production authorization or permission to
merge. Empty/all-skipped test selections and invalid evidence fail. Artifact names
and failing step summaries point to sanitized diagnostics. Do not paste environment
or credential dumps into public issues. No AWS/model/production credentials are
needed. Existing coursework reference links are intentionally deferred in hosted
validation; unrelated links must resolve inside the project.

## Security and releases

Use the [vulnerability register](VULNERABILITY_REGISTER.md) and explicit, expiring
owner risk decisions. Never edit a baseline to silently accept new findings or
renew dates without approval. CI preserves all findings and rejects new/fixable/
escalated/known-exploited or unaccepted risk. Production remains blocked.

Ruleset changes require separate approval after actual check contexts exist. The
current active ruleset is not proof that required checks have been selected.

Future releases need reviewed semantic versions, changelog, immutable source/image
identity, migration/rollback and restore evidence, privacy/hosting approval and
protected deployment controls. No P1-05 release/tag/deployment is authorized.
Revert or forward-fix through a reviewed PR; never rewrite main to hide mistakes.
