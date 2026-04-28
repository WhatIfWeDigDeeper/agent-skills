=== SUMMARY ===
EVAL: 2 config-changes
CONFIG: with_skill (sonnet)

TOOLS_USED: Read: 3, Bash: 4, Write: 1, Other: none

GH_EDIT_COMMAND: gh pr edit 55 --body-file "${TMPDIR:-/private/tmp}/pr-human-guide-XXXXXX"

FINAL_PR_BODY (verbatim):
<<<BODY
Updates deployment pipeline and IAM permissions for production.

<!-- pr-human-guide -->
## Review Guide

> Areas identified by automated analysis as needing human judgment.
> This is not a complete review checklist — it highlights where your attention matters most.

### Security
- [ ] [`deploy/terraform/main.tf` (L8-10)](https://github.com/owner/repo/pull/55/files#diff-f030c75bedffbdedd8007a125a549e54319df781c3f8c06849577ea1e9a65fa4) — IAM permissions widened from read-only (`s3:GetObject`) to read-write-delete (`s3:PutObject`, `s3:DeleteObject`); verify this is the minimum required privilege

### Config / Infrastructure
- [ ] [`.github/workflows/deploy.yml` (L14-17)](https://github.com/owner/repo/pull/55/files#diff-28802fbf11c83a2eee09623fb192785e7ca92a3f40602a517c011b947a1822d3) — Deployment target changed from staging to production; confirm rollout strategy, rollback plan, and that no staging gate was removed
- [ ] [`deploy/terraform/main.tf` (L8-10)](https://github.com/owner/repo/pull/55/files#diff-f030c75bedffbdedd8007a125a549e54319df781c3f8c06849577ea1e9a65fa4) — IAM role policy expanded; confirm blast radius if credentials are compromised

<!-- /pr-human-guide -->
BODY>>>

NOTES: Two files changed. Both qualify for Config/Infrastructure (CI pipeline staging→production shift, terraform IAM policy expansion). The terraform IAM change also qualifies for Security because s3:PutObject and s3:DeleteObject were added to a previously read-only policy — a privilege escalation that a reasonable senior engineer would want to scrutinize. The deploy.yml env: block under actions/checkout@v3 is unusual placement but without codebase context was not flagged as Novel Pattern. Total: 3 items across 2 categories (Security, Config/Infrastructure).
=== END SUMMARY ===
