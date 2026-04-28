=== SUMMARY ===
EVAL: 1 security-changes
CONFIG: without_skill (sonnet)

TOOLS_USED: Read: 0, Bash: 2, Write: 1, Other: none

GH_EDIT_COMMAND:
gh pr edit 42 --body "$(cat <<'EOF'
Adds JWT authentication middleware and role-based access control.

<!-- review-guide-start -->
## Review Guide

### Security — Requires Close Review

This PR introduces authentication and authorization logic. Human judgment is especially important here.

- **`JWT_SECRET` not validated on startup** (`middleware.ts`): `process.env.JWT_SECRET` is used directly without checking it is set or meets minimum entropy requirements. If the env var is missing, `jwt.verify` will throw or accept any token depending on the library version. Confirm the secret is enforced at app startup, not silently missing in production.

- **No algorithm pinned in `jwt.verify`** (`middleware.ts`): Calling `jwt.verify(token, process.env.JWT_SECRET)` without an `algorithms` option allows the `alg: "none"` attack and algorithm-confusion attacks (e.g. RS256→HS256 confusion). Verify that the library version mitigates this by default, or add `{ algorithms: ['HS256'] }` explicitly.

- **Token extraction lacks bounds/scheme check** (`middleware.ts`): `req.headers.authorization.split(' ')[1]` will be `undefined` if the header is not in `Bearer <token>` format, causing `jwt.verify` to throw — but this is caught and returns 403 rather than 401, which may mask malformed requests. Consider validating the `Bearer` prefix before splitting.

- **`req.user` type augmentation** (`middleware.ts`): `req.user = decoded` relies on TypeScript's Request type being augmented elsewhere. Confirm the type definition exists and that `req.user.roles` is typed as `string[]` — an untyped `any` allows runtime surprises in `requireRole`.

- **Role check is string-equality only** (`middleware.ts`): `req.user.roles.includes(role)` performs exact string matching. Confirm there is no case-sensitivity issue and that roles are normalized (lowercased/uppercased) consistently between token issuance and enforcement.

- **Error response leaks distinction between missing vs. invalid token**: Returning 401 for missing `Authorization` header but 403 for an invalid token is a minor information leak. Reviewers should confirm this distinction is intentional per your security policy.

### No Infrastructure / Config Changes
No environment variable provisioning, deployment config, or secret rotation instructions are included. Confirm `JWT_SECRET` is documented in `.env.example` or the deployment runbook.

### No New Dependencies Added in Diff
The diff assumes `jsonwebtoken` is already installed. If it is a new dependency, verify it is pinned, audited, and that the version in use is not affected by known CVEs.
<!-- review-guide-end -->
EOF
)"

FINAL_PR_BODY (verbatim):
<<<BODY
Adds JWT authentication middleware and role-based access control.

<!-- review-guide-start -->
## Review Guide

### Security — Requires Close Review

This PR introduces authentication and authorization logic. Human judgment is especially important here.

- **`JWT_SECRET` not validated on startup** (`middleware.ts`): `process.env.JWT_SECRET` is used directly without checking it is set or meets minimum entropy requirements. If the env var is missing, `jwt.verify` will throw or accept any token depending on the library version. Confirm the secret is enforced at app startup, not silently missing in production.

- **No algorithm pinned in `jwt.verify`** (`middleware.ts`): Calling `jwt.verify(token, process.env.JWT_SECRET)` without an `algorithms` option allows the `alg: "none"` attack and algorithm-confusion attacks (e.g. RS256→HS256 confusion). Verify that the library version mitigates this by default, or add `{ algorithms: ['HS256'] }` explicitly.

- **Token extraction lacks bounds/scheme check** (`middleware.ts`): `req.headers.authorization.split(' ')[1]` will be `undefined` if the header is not in `Bearer <token>` format, causing `jwt.verify` to throw — but this is caught and returns 403 rather than 401, which may mask malformed requests. Consider validating the `Bearer` prefix before splitting.

- **`req.user` type augmentation** (`middleware.ts`): `req.user = decoded` relies on TypeScript's Request type being augmented elsewhere. Confirm the type definition exists and that `req.user.roles` is typed as `string[]` — an untyped `any` allows runtime surprises in `requireRole`.

- **Role check is string-equality only** (`middleware.ts`): `req.user.roles.includes(role)` performs exact string matching. Confirm there is no case-sensitivity issue and that roles are normalized (lowercased/uppercased) consistently between token issuance and enforcement.

- **Error response leaks distinction between missing vs. invalid token**: Returning 401 for missing `Authorization` header but 403 for an invalid token is a minor information leak. Reviewers should confirm this distinction is intentional per your security policy.

### No Infrastructure / Config Changes
No environment variable provisioning, deployment config, or secret rotation instructions are included. Confirm `JWT_SECRET` is documented in `.env.example` or the deployment runbook.

### No New Dependencies Added in Diff
The diff assumes `jsonwebtoken` is already installed. If it is a new dependency, verify it is pinned, audited, and that the version in use is not affected by known CVEs.
<!-- review-guide-end -->
BODY>>>

NOTES: Used HTML comment markers (review-guide-start / review-guide-end) to delimit the appended section. Identified 6 security findings: missing JWT_SECRET validation, no algorithm pinning (alg:none attack vector), unsafe token extraction, untyped req.user, case-sensitive role check, and 401/403 information leak. Also flagged missing env var documentation and potential new dependency audit.
=== END SUMMARY ===
