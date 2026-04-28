=== SUMMARY ===
EVAL: 2 config-changes
CONFIG: without_skill (opus)

TOOLS_USED: Read: 0, Bash: 2, Write: 1, Other: none

GH_EDIT_COMMAND: did not run

FINAL_PR_BODY (verbatim):
<<<BODY
Updates deployment pipeline and IAM permissions for production.

## Summary of changes

- `.github/workflows/deploy.yml`: renames the deploy step from "Deploy to staging" to "Deploy to production" and adds environment variables `AWS_REGION=us-east-1` and `DEPLOY_ENV=production`.
- `deploy/terraform/main.tf`: expands the IAM role policy for `aws_iam_role_policy.app_policy` from `s3:GetObject` only to also include `s3:PutObject` and `s3:DeleteObject` on `arn:aws:s3:::my-app-bucket/*`.

## Human review guide

The changes here touch production infrastructure and IAM blast radius. Please pay extra attention to the following areas — automated checks cannot validate intent or org policy on these.

### Security / IAM (high priority)
- **Privilege expansion on S3**: the policy now grants `s3:PutObject` and `s3:DeleteObject` in addition to `s3:GetObject`. Confirm the application actually needs write and delete on `my-app-bucket/*`. If only writes are required, drop `s3:DeleteObject`. If deletes are needed only under a prefix, scope the resource (e.g. `arn:aws:s3:::my-app-bucket/uploads/*`) instead of `*`.
- **No `Condition` block**: consider adding conditions (e.g. `aws:SecureTransport`, source VPC, or object tag constraints) to limit how the new permissions can be used.
- **Bucket sensitivity**: verify `my-app-bucket` does not contain data whose deletion would be unrecoverable (no versioning / no MFA-delete). If versioning is off, `s3:DeleteObject` is destructive and irreversible.
- **Audit / least privilege**: confirm this role is not assumed by humans or unrelated services — broadening it expands blast radius for every principal that can assume it.

### Config / infrastructure (high priority)
- **Staging → production rename**: the workflow step previously named "Deploy to staging" is now "Deploy to production". Verify this is an intentional promotion of this workflow to deploy to prod, and not an accidental rename that will cause the next merge to `main` to push to production. If staging deploys are still needed, they must live in a separate job/workflow.
- **`DEPLOY_ENV=production` and `AWS_REGION=us-east-1` hardcoded**: hardcoding the environment in the workflow removes the ability to dry-run or deploy to a non-prod environment from this workflow. Confirm there is a separate, gated path for staging.
- **Trigger conditions**: check the rest of `deploy.yml` (not shown in this diff) — what events trigger this workflow? If it runs on every push to `main` or on PR merge without an environment protection rule / required reviewers, every merged PR will now ship to production automatically.
- **Secrets / credentials**: the new `env:` block sets region and env name but does not show how AWS credentials are obtained. Confirm credentials come from OIDC / GitHub environment secrets scoped to a `production` environment with required reviewers, not from a long-lived access key.
- **`actions/checkout@v3` is pinned to a major tag**, not a SHA. For a production-deploy workflow, consider pinning to a commit SHA to prevent supply-chain drift.
- **Step ordering looks suspicious**: the step named "Deploy to production" uses `actions/checkout@v3`, which is a checkout action, not a deploy action. Worth confirming this is not a copy/paste artifact and that the actual deploy logic exists in a later step that the diff does not show.

### Operational / rollback
- **No visible plan/apply gating** on the Terraform change in this diff. Confirm `terraform plan` is reviewed before `apply`, and that state is locked.
- **Rollback story**: if the IAM expansion causes an incident, reverting this PR removes the permissions but does not undo any `PutObject` / `DeleteObject` calls already made. Worth noting for the on-call.

### Suggested questions for the reviewer to answer before approving
1. Is this workflow intentionally being promoted from staging to production, or should the staging step be preserved as a separate job?
2. Does the application genuinely need `s3:DeleteObject`, or would `s3:PutObject` alone suffice?
3. Is `my-app-bucket` versioned, and is there a GitHub environment protection rule on `production`?
4. Are AWS credentials provisioned via OIDC, and is the role trust policy scoped to this repo + the `production` environment?
BODY>>>

NOTES: Without the skill loaded I produced a review guide directly from the diff. I focused on the two highest-risk dimensions for this change — IAM privilege expansion (Put/Delete added on a wildcard resource) and the staging→production workflow rename plus hardcoded `DEPLOY_ENV=production`. I also flagged the suspicious step body (a step labeled "Deploy to production" whose `uses:` is `actions/checkout@v3`) since that may indicate the diff is incomplete or the step is mis-wired. No `gh` commands were executed per the simulation rules; the body above is what I would pass to `gh pr edit 55 --body-file ...`.
=== END SUMMARY ===
