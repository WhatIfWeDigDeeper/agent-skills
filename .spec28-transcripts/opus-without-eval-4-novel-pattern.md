=== SUMMARY ===
EVAL: 4 novel-pattern
CONFIG: without_skill (opus)

TOOLS_USED: Read: 0, Bash: 2, Write: 1, Other: none

GH_EDIT_COMMAND: did not run

FINAL_PR_BODY (verbatim):
<<<BODY
Adds payment processing service using Result type pattern.

---

## Review guide

This PR introduces a payment processing service. Because it touches money, an external API (Stripe), and introduces a new error-handling style, please pay close attention to the items below.

### Novel pattern — diverges from the rest of the codebase

- **`Result<T, E>` from `ts-results`** is introduced here for the first time. The rest of `src/services/` (e.g. `user.ts`, `product.ts`, `order.ts`) uses `try` / `catch` and re-throws `AppError`. Reviewers should decide whether:
  - the codebase is intentionally migrating to `Result` (in which case we need a written convention and a migration plan), or
  - this file should be rewritten to match the existing `AppError` pattern for consistency.
- Mixing the two styles silently is the worst outcome — callers of `processPayment` / `refundPayment` will need to know to check `.err` / `.val` instead of using `try`/`catch`, which is easy to get wrong.

### New dependency

- **`ts-results`** is a new runtime dependency. Please confirm:
  - it is added to `package.json` (and the lockfile) in this PR,
  - license is acceptable,
  - maintenance status / last release date is healthy,
  - there isn't an already-approved equivalent in the repo we should use instead.

### Likely bugs — please verify before merge

1. **`refundPayment` does not actually refund.** It calls `processPayment(0)`, which would create a new $0 charge via `stripe.charges.create`, not issue a refund against `chargeId`. The expected call is something like `stripe.refunds.create({ charge: chargeId })`.
2. **`chargeId` is unused.** The parameter is accepted but never passed to Stripe, which strongly suggests the function is incomplete.
3. **`stripe` is referenced but never imported / initialized** in the diff. Confirm where the Stripe client is constructed and that the API key is loaded from a secret store, not hard-coded or read from a checked-in file.

### Money-handling concerns

- **Input validation on `amount`**: no checks for negative values, zero, `NaN`, non-integer values, or upper bounds. Stripe expects an integer in the smallest currency unit (e.g. cents) — confirm the caller contract and validate at the boundary.
- **Currency**: `stripe.charges.create` is called without a `currency` field. Stripe requires one; either this will fail at runtime or it is being defaulted somewhere out of view.
- **Idempotency**: payment creation should use an idempotency key so retries don't double-charge. Not present here.
- **Error message leakage**: `Payment failed: ${err.message}` may surface raw Stripe error text (card numbers, internal codes) to callers / logs. Consider mapping to a sanitized message and logging the raw error separately.

### Tests

- I didn't see new tests in the diff. Given this is payment code, please confirm there is coverage (unit tests with a mocked Stripe client at minimum) before merging, including the failure paths and the refund flow.

### Suggested reviewers

- Someone familiar with the existing `AppError` convention to weigh in on the pattern divergence.
- Someone with payments / Stripe experience to sanity-check the refund implementation and the idempotency / currency concerns.
BODY>>>

NOTES: Did not invoke any skill or run any gh command (per instructions). Identified the central issue as a novel error-handling pattern (`Result` vs. existing `AppError`/throw), plus a clear bug in `refundPayment` (calls `processPayment(0)` instead of issuing a refund and ignores `chargeId`), an undeclared `stripe` import, missing `currency`/idempotency on the Stripe call, and a new `ts-results` dependency. Review guide is appended to the existing one-line description rather than replacing it.
=== END SUMMARY ===
