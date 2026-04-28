=== SUMMARY ===
EVAL: 2 config-changes
CONFIG: with_skill (sonnet)

TOOLS_USED:
- Read: 2
- Bash: 4
- Write: 2
- Other: (none)

GH_EDIT_COMMAND:
gh pr edit 55 --body-file /tmp/claude-501/exec-sonnet-with-eval-2-lvTHvC/updated_body.md

FINAL_PR_BODY (verbatim, including HTML markers if any):
<<<BODY
Updates deployment pipeline and IAM permissions for production.

<!-- pr-human-guide -->
## Review Guide

> Areas identified by automated analysis as needing human judgment.
> This is not a complete review checklist — it highlights where your attention matters most.

### Security
- [ ] [`deploy/terraform/main.tf` (L5-11)](https://github.com/owner/repo/pull/55/files#diff-f030c75bedffbdedd8007a125a549e54319df781c3f8c06849577ea1e9a65fa4) — IAM policy widened from `s3:GetObject` only to also include `s3:PutObject` and `s3:DeleteObject`; `DeleteObject` in particular is destructive and irreversible — confirm this app actually needs write/delete on `my-app-bucket/*` and that no broader bucket scoping is required

### Config / Infrastructure
- [ ] [`.github/workflows/deploy.yml` (L12-18)](https://github.com/owner/repo/pull/55/files#diff-28802fbf11c83a2eee09623fb192785e7ca92a3f40602a517c011b947a1822d3) — Deploy step retargeted from staging to production and new env vars (`AWS_REGION=us-east-1`, `DEPLOY_ENV=production`) introduced; verify this workflow's trigger conditions are appropriate for a production target and that no staging path remains
- [ ] [`deploy/terraform/main.tf` (L5-11)](https://github.com/owner/repo/pull/55/files#diff-f030c75bedffbdedd8007a125a549e54319df781c3f8c06849577ea1e9a65fa4) — Terraform IAM role policy change; confirm the bucket ARN scope (`my-app-bucket/*`) is intentional and that least-privilege is preserved given the added write/delete actions

<!-- /pr-human-guide -->
BODY>>>

NOTES:
- PR is simulated; no actual gh commands executed.
- 3 items across 2 categories: Security (1), Config / Infrastructure (2).
- `deploy/terraform/main.tf` appears in both Security and Config / Infrastructure per categories.md rule that distinct concerns get separate entries across categories.
- Anchors computed via `printf '%s' "<path>" | shasum -a 256`.
=== END SUMMARY ===
