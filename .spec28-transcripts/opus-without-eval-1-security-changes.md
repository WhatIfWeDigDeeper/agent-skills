=== SUMMARY ===
EVAL: 1 security-changes
CONFIG: without_skill (opus)

TOOLS_USED: Read: 0, Bash: 2, Write: 1, Other: none

GH_EDIT_COMMAND: gh pr edit 42 --body-file [redacted-temp-path]

FINAL_PR_BODY (verbatim):
<<<BODY
Adds JWT authentication middleware and role-based access control.

## Review Guide

This PR introduces authentication and authorization primitives. Because these are security-critical, please review the following areas closely.

### Security — high priority

- **JWT verification has no algorithm allowlist.** `jwt.verify(token, process.env.JWT_SECRET)` accepts whatever algorithm the token claims. Without an explicit `{ algorithms: ['HS256'] }` (or whatever we standardize on), an attacker can swap algorithms (classic `alg: none` / RS256↔HS256 confusion). Please confirm we pin the algorithm.
- **`JWT_SECRET` is read at call time with no validation.** If `process.env.JWT_SECRET` is undefined (misconfigured env), `jwt.verify` behavior is surprising and may not fail closed in all `jsonwebtoken` versions. Recommend validating presence at startup and failing fast.
- **Authorization header parsing is fragile.** `req.headers.authorization.split(' ')[1]` does not check for the `Bearer` scheme and yields `undefined` for malformed headers (e.g. a single token with no space). `jwt.verify(undefined, ...)` will throw and be caught, so it fails closed — but please confirm the intended behavior and consider explicitly validating the `Bearer <token>` shape.
- **403 vs 401 semantics.** Invalid/expired tokens currently return 403 ("Forbidden"); convention is 401 ("Unauthorized") for authentication failures and 403 for authorization (role) failures. Worth aligning so clients can distinguish "log in again" from "you don't have access."
- **`requireRole` assumes `req.user.roles` is an array.** If a token's payload is missing `roles` or it's not an array, `req.user.roles.includes(role)` throws and surfaces as a 500 rather than a clean 403. Suggest `Array.isArray(req.user?.roles) && req.user.roles.includes(role)`.
- **Single-role check only.** `requireRole(role: string)` accepts one role; common needs (admin override, "any of these roles") aren't supported. Confirm this matches product requirements.

### Type safety

- **`req.user = decoded`** — `decoded` from `jwt.verify` is typed as `string | JwtPayload`. Assigning it to `req.user` likely requires a module augmentation for `Express.Request` and a runtime check that `decoded` is an object (not a string). Please confirm the `Request` type is augmented somewhere in the repo.

### Testing & observability

- No tests are included in this diff. Given this is auth-critical code, please add coverage for: missing header, malformed header, expired token, tampered signature, wrong algorithm, missing `roles` claim, role match / mismatch.
- Consider whether auth failures should be logged (with care not to log the token itself) for security monitoring.

### Operational

- Rate limiting on endpoints protected by `requireAuth` is not visible here — confirm it exists upstream, or note as a follow-up.
- Token expiry / refresh flow isn't part of this PR; flagging so reviewers know to check it lives elsewhere.

---

Reviewers: please pay particular attention to the algorithm-pinning and `JWT_SECRET` validation items — those are the highest-impact concerns.
BODY>>>

NOTES: Did not execute gh; command shown is what would run. Identified algorithm-confusion risk, missing JWT_SECRET validation, fragile header parsing, 401 vs 403 semantics, unsafe roles access, missing tests, and TS Request augmentation as the key reviewer-attention items.
=== END SUMMARY ===
