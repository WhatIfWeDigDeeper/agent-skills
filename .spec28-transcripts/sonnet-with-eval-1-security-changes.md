=== SUMMARY ===
EVAL: 1 security-changes
CONFIG: with_skill (sonnet)

TOOLS_USED:
- Read: 2
- Bash: 3
- Write: 2
- Other: none

GH_EDIT_COMMAND:
gh pr edit 42 --body-file /tmp/claude-501/exec-sonnet-with-eval-1-1jRwCc/pr-body.md

FINAL_PR_BODY (verbatim, including HTML markers if any):
<<<BODY
Adds JWT authentication middleware and role-based access control.

<!-- pr-human-guide -->
## Review Guide

> Areas identified by automated analysis as needing human judgment.
> This is not a complete review checklist — it highlights where your attention matters most.

### Security
- [ ] [`src/auth/middleware.ts` (L41-56)](https://github.com/owner/repo/pull/42/files#diff-e67371ea94bae31fbe0781e9d8777c9b44a1471d7dbd27d444ecd73ac826eb82) — JWT token verification using `process.env.JWT_SECRET` and new `requireRole` authorization middleware; verify secret handling, token-validation error paths, and role-check semantics

<!-- /pr-human-guide -->
BODY>>>

NOTES:
- categories evaluated: 6, flagged: 1 Security
- Single file (src/auth/middleware.ts) with two adjacent flagged regions (JWT verify hunk + new requireRole function) merged into one entry per consolidation rule
- No new dependencies added in diff (jwt import not shown as new); no schema/IaC/concurrency changes
- Diff anchor SHA-256: e67371ea94bae31fbe0781e9d8777c9b44a1471d7dbd27d444ecd73ac826eb82
=== END SUMMARY ===
