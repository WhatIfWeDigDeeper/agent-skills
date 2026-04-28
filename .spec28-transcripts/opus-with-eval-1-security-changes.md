=== SUMMARY ===
EVAL: 1 security-changes
CONFIG: with_skill (opus)

TOOLS_USED: Read: 2, Bash: 3, Write: 1, Other: Edit (none)

GH_EDIT_COMMAND:
gh pr edit 42 --body-file "$TMPFILE"

(where $TMPFILE is created via `mktemp "${TMPDIR:-/private/tmp}/pr-human-guide-XXXXXX"` and populated with the FINAL_PR_BODY content below)

FINAL_PR_BODY (verbatim):
<<<BODY
Adds JWT authentication middleware and role-based access control.

<!-- pr-human-guide -->
## Review Guide

> Areas identified by automated analysis as needing human judgment.
> This is not a complete review checklist — it highlights where your attention matters most.

### Security
- [ ] [`src/auth/middleware.ts` (L42-58)](https://github.com/owner/repo/pull/42/files#diff-e67371ea94bae31fbe0781e9d8777c9b44a1471d7dbd27d444ecd73ac826eb82R42-R58) — New JWT token verification using `process.env.JWT_SECRET` (no algorithm pin, no audience/issuer checks, missing-token edge cases) and new `requireRole` authorization middleware — confirm threat model, secret rotation story, and that `req.user.roles` is trusted only after `requireAuth` has run.

<!-- /pr-human-guide -->
BODY>>>

NOTES:
- Single changed file (`src/auth/middleware.ts`); diff modifies an existing file (`index a1b2c3d..e4f5a6b`), so Novel Patterns guidance for "new directory with no siblings" does not apply. Per selectivity threshold, kept the entry under Security only — the JWT verify + RBAC concerns are the load-bearing reviewer judgment calls and Novel Patterns would be speculative without sibling context.
- Merged the token-verify block (new L42-48) and the new `requireRole` function (new L50-58) into a single Security entry per consolidation rule (regions adjacent / within 20 lines).
- Diff anchor SHA-256 for `src/auth/middleware.ts`: `e67371ea94bae31fbe0781e9d8777c9b44a1471d7dbd27d444ecd73ac826eb82` (computed via `printf "%s" "src/auth/middleware.ts" | shasum -a 256`).
- No existing `<!-- pr-human-guide -->` markers in the current PR description, so the guide is appended (not replacing).
- All `gh` commands simulated per instructions; no real GitHub calls executed.
=== END SUMMARY ===
