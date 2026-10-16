## Problem and resulting change

Explain the concrete problem, final behavior/design, and why this change is needed.
Link the issue, requirement IDs and ADRs. Identify the approved phase and scope.

## Validation

List exact commands and actual outcomes. Distinguish local results from GitHub
Actions results, and offline fixtures from live calls. Mark unavailable checks as
not run with a reason; do not report skipped application tests as passes.

For diagrams, identify the Mermaid version and whether syntax, generated rendering,
and visual inspection were verified. Do not attach secrets or private data.

## Design, security and rollout

Describe important tradeoffs, compatibility/migration impact, ownership checks,
privacy/bilingual/accessibility impact, limitations and rollback where applicable.
For documentation-only changes, explain any changed requirements or assumptions.

## Review checklist

- [ ] The change stays within approved scope and uses a feature branch.
- [ ] Commit messages follow Conventional Commits.
- [ ] Documentation/contracts/diagrams are consistent; relevant checks passed.
- [ ] Implementation changes have meaningful tests, or this is documentation/tooling only.
- [ ] Staged/tracked files contain no secrets, private datasets or coursework.
- [ ] Security and privacy implications and outstanding decisions are recorded.
- [ ] Blocking review comments are resolved; user approval is required before merge.
- [ ] No automatic start of another phase or unapproved deployment/release.
