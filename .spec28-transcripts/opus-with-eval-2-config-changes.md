=== SUMMARY ===
EVAL: 2 config-changes
CONFIG: with_skill (opus)

TOOLS_USED: Read: 2, Bash: 3, Write: 2, Other: none

GH_EDIT_COMMAND: gh pr edit 55 --body-file /tmp/claude-501/exec-opus-with-eval-2-6Nn8lG/body.md

FINAL_PR_BODY (verbatim):
<<<BODY
Updates deployment pipeline and IAM permissions for production.

<!-- pr-human-guide -->
## Review Guide

> Areas identified by automated analysis as needing human judgment.
> This is not a complete review checklist — it highlights where your attention matters most.

### Security
- [ ] [`deploy/terraform/main.tf` (L5-12)](https://github.com/owner/repo/pull/55/files#diff-f030c75bedffbdedd8007a125a549e54319df781c3f8c06849577ea1e9a65fa4) — IAM policy widened from read-only (`s3:GetObject`) to include `s3:PutObject` and `s3:DeleteObject`; confirm scope and resource ARN are appropriate, and consider blast radius if credentials are compromised

### Config / Infrastructure
- [ ] [`.github/workflows/deploy.yml` (L12-18)](https://github.com/owner/repo/pull/55/files#diff-28802fbf11c83a2eee09623fb192785e7ca92a3f40602a517c011b947a1822d3) — Deploy step retargeted from staging to production with hardcoded `AWS_REGION` and `DEPLOY_ENV`; verify gating, approvals, and that staging coverage isn't lost
- [ ] [`deploy/terraform/main.tf` (L5-12)](https://github.com/owner/repo/pull/55/files#diff-f030c75bedffbdedd8007a125a549e54319df781c3f8c06849577ea1e9a65fa4) — IAM role policy expansion affects production permissions

<!-- /pr-human-guide -->
BODY>>>

NOTES: Two files flagged across two categories. main.tf appears in both Security (IAM permission widening at trust boundary — adds write/delete on S3) and Config/Infrastructure (Terraform IAM policy). deploy.yml flagged as Config/Infrastructure (CI/CD pipeline retargeted from staging to production with hardcoded env vars). No new dependencies, data model, novel pattern, or concurrency concerns. SHA-256 anchors computed for both file paths. PR body preserves the original one-line description and appends the guide between idempotent <!-- pr-human-guide --> markers.
=== END SUMMARY ===
