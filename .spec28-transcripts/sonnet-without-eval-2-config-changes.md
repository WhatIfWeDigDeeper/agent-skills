=== SUMMARY ===
EVAL: 2 config-changes
CONFIG: without_skill (sonnet)

TOOLS_USED: Read: 0, Bash: 2, Write: 1, Other: none

GH_EDIT_COMMAND:
gh pr edit 55 --repo owner/repo --body 'Updates deployment pipeline and IAM permissions for production.

---

## Human Review Guide

This PR makes infrastructure and security-sensitive changes that require careful human judgment before merging.

### Security / IAM Permissions

**`deploy/terraform/main.tf` — IAM policy expansion**

The S3 bucket policy for `my-app-bucket` has been upgraded from read-only to read-write-delete:

- Added: `s3:PutObject` — allows the application to write new objects to the bucket
- Added: `s3:DeleteObject` — allows the application to permanently delete objects from the bucket

**Review checklist:**
- Is it intentional for the application to have delete permissions on this bucket? Destructive S3 permissions are irreversible once exercised.
- Does the application actually require write/delete access, or is this broader than needed (principle of least privilege)?
- Is the bucket protected by versioning or Object Lock if delete permissions are granted?
- Are there any data retention or compliance requirements that conflict with allowing deletions?

### Config / Infrastructure

**`.github/workflows/deploy.yml` — Production deployment target**

The deployment workflow has been changed from staging to production:

- Renamed step: `Deploy to staging` → `Deploy to production`
- Added environment variables: `AWS_REGION: us-east-1` and `DEPLOY_ENV: production`

**Review checklist:**
- Is this workflow now targeting the live production environment? Confirm this is intentional and that staging still has a separate workflow.
- Are the hardcoded values (`us-east-1`, `production`) correct for the intended deployment target?
- Should `DEPLOY_ENV` and `AWS_REGION` be stored as secrets or repository variables rather than hardcoded in the workflow file?
- Does this workflow have appropriate gates (e.g. approval steps, environment protection rules) before deploying to production?
- Is there a rollback plan if the production deployment fails?'

FINAL_PR_BODY (verbatim):
<<<BODY
Updates deployment pipeline and IAM permissions for production.

---

## Human Review Guide

This PR makes infrastructure and security-sensitive changes that require careful human judgment before merging.

### Security / IAM Permissions

**`deploy/terraform/main.tf` — IAM policy expansion**

The S3 bucket policy for `my-app-bucket` has been upgraded from read-only to read-write-delete:

- Added: `s3:PutObject` — allows the application to write new objects to the bucket
- Added: `s3:DeleteObject` — allows the application to permanently delete objects from the bucket

**Review checklist:**
- Is it intentional for the application to have delete permissions on this bucket? Destructive S3 permissions are irreversible once exercised.
- Does the application actually require write/delete access, or is this broader than needed (principle of least privilege)?
- Is the bucket protected by versioning or Object Lock if delete permissions are granted?
- Are there any data retention or compliance requirements that conflict with allowing deletions?

### Config / Infrastructure

**`.github/workflows/deploy.yml` — Production deployment target**

The deployment workflow has been changed from staging to production:

- Renamed step: `Deploy to staging` → `Deploy to production`
- Added environment variables: `AWS_REGION: us-east-1` and `DEPLOY_ENV: production`

**Review checklist:**
- Is this workflow now targeting the live production environment? Confirm this is intentional and that staging still has a separate workflow.
- Are the hardcoded values (`us-east-1`, `production`) correct for the intended deployment target?
- Should `DEPLOY_ENV` and `AWS_REGION` be stored as secrets or repository variables rather than hardcoded in the workflow file?
- Does this workflow have appropriate gates (e.g. approval steps, environment protection rules) before deploying to production?
- Is there a rollback plan if the production deployment fails?
BODY>>>

NOTES: Two high-risk change categories identified: (1) IAM permission expansion from read-only to read-write-delete on S3 — flagged for least-privilege and data-safety review; (2) CI/CD workflow retargeted from staging to production with hardcoded env vars — flagged for environment protection rules and secrets management. No new dependencies or data model changes present.
=== END SUMMARY ===
