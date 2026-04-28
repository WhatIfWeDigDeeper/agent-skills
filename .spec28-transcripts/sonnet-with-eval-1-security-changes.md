=== SUMMARY ===
EVAL: 1 security-changes
CONFIG: with_skill (sonnet)

TOOLS_USED: Read: 2, Bash: 3, Write: 1, Other: none

GH_EDIT_COMMAND: gh pr edit 42 --body-file "${TMPDIR:-/private/tmp}/pr-human-guide-body.txt"

FINAL_PR_BODY (verbatim):
<<<BODY
Adds JWT authentication middleware and role-based access control.

<!-- pr-human-guide -->
## Review Guide

> Areas identified by automated analysis as needing human judgment.
> This is not a complete review checklist — it highlights where your attention matters most.

### Security
- [ ] [`src/auth/middleware.ts` (L41-61)](https://github.com/owner/repo/pull/42/files#diff-e67371ea94bae31fbe0781e9d8777c9b44a1471d7dbd27d444ecd73ac826eb82R41) — JWT token extraction, validation, and role-based access checks; verify token algorithm is restricted (e.g. no `alg: none`), error messages don't leak details, and role check covers all protected routes

<!-- /pr-human-guide -->
BODY>>>

NOTES: Single file changed (src/auth/middleware.ts). Flagged under Security only — both the JWT validation block and the requireRole RBAC function qualify (token validation, authorization/role checks per categories.md). No config/infra, new dependencies, data model, or concurrency signals present. Line range L41-61 derived from diff hunk @@ -38,6 +38,24 @@ placing new lines at 41-61. SHA-256 anchor computed via `printf '%s' "src/auth/middleware.ts" | shasum -a 256`. Used Python to construct HTML comment markers to avoid zsh `!` history expansion corruption.
=== END SUMMARY ===
