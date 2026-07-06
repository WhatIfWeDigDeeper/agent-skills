# Spec 51: pr-comments — regression test with every substantive code fix

## Context

GitHub issue [#204](https://github.com/WhatIfWeDigDeeper/agent-skills/issues/204):
when `pr-comments` classifies a review comment as `fix` and the fix touches
code, the skill implements and commits the fix but does **not** add a regression
test guarding it. In a recent run the code fixes were committed test-less; the
tests only arrived a commit later, after the user explicitly asked "should we
add tests for the code-related fixes?" A review fix without a test invites the
same regression back.

The rule is cross-cutting (not tied to any one project), and the skill is
vendored via `skills-lock.json`, so a local edit would be overwritten on the
next sync — it belongs in the shared skill.

### Current reality (verified before writing this spec)

- `skills/pr-comments/SKILL.md`: **version `1.49`**, **491 lines**.
- Fix pipeline: **Step 6** (classify `fix` / `accept suggestion` / `reply` /
  `decline` / `skip`, then tag `nit`) → **Step 7** (present plan / confirm) →
  **Step 8** (**Apply Changes** — the actual edit pass) → **Step 9** (post-edit
  drift re-scan) → **Step 10** (commit with commenter credit).
- **No test-adding rule exists** anywhere in SKILL.md or its `references/*.md`;
  the word "regression" does not appear. The only test mention is Step 6's
  "reproduce it against the current file/tests first" — used to verify a
  falsifiable claim *before* classifying `fix`, not to guard a fix afterward.
- Step 6 already produces the exact predicate the new rule keys off: the **`nit`
  tag**, defined as "clearly cosmetic/trivial — no effect on correctness,
  behavior, security, performance, or public API." Non-`nit`
  `fix` / `accept suggestion` rows are the substantive edits a regression test
  should guard. The tag "only modifies `fix` / `accept suggestion`" —
  `reply` / `decline` / `skip` / `consistency` are never nits.
- `tests/pr-comments/` models classifiable predicates in `conftest.py` (e.g.
  `is_nit(body, action)`), one test file per concern (e.g. `test_nit_gate.py`).
  The new behavior maps onto a `requires_regression_test(...)` predicate layered
  on `is_nit`.

## Goals

1. When `pr-comments` applies a **substantive code-level fix**, it adds or
   updates a regression test **in the same commit** — so the fix and its guard
   land together, not a commit (or a user nudge) later.
2. Follow **test-first (TDD)** ordering: write/extend the test **before** the
   code change, confirm it **fails** for the expected reason (red), then apply
   the fix and confirm it **passes** (green).
3. Scope the rule so it doesn't become noise: skip `nit` rows and non-code
   changes; skip `reply` / `decline` / `skip`.
4. Keep the environment realistic: if the test can't be executed here, validate
   through whatever harness is available and say so — don't drop the test.
5. Cover the rule with unit tests, consistent with the existing
   `tests/pr-comments/` predicate-modeling pattern.

## Decisions (confirmed with user)

1. **Scope:** the rule fires for both manual `fix` **and** accepted `suggestion`
   edits that touch behavior — any non-`nit` code-level change. (Not just the
   literal `fix` action.)
2. **Deliverable:** SKILL.md rule **+ unit tests** under `tests/pr-comments/`.
   Evals are **deferred to a follow-up** (not in this spec).
3. **Strictness:** **strong default + fallback** (judgment-based), not a hard
   commit-blocking gate. Add/update a regression test in the same commit; if the
   environment can't run the test, validate via the available harness and note
   it in the commit/reply.
4. **TDD ordering:** the test is written **first** and confirmed failing before
   the code change that makes it pass (red → green), in the same commit.
5. **Manual mode:** no separate confirmation for the test. Rows that will get a
   regression test are flagged in the Step 7 plan table for visibility; the
   existing `Proceed? [y/N/auto]` gate confirms the fix and its test together.

## Design

### Step 8 — the new rule (primary change)

Add the rule inline in **Step 8 (Apply Changes)**, immediately after the
sentence "Apply all changes in a single pass… Track which thread and login
correspond to each change." (phrase anchor). Step 8 is where the edit pass
happens and can reference the `nit` tag Step 6 already assigned. Keep it inline
(~14–20 lines) — under the `skills/CLAUDE.md` threshold for extracting a
reference file.

Rule content:

- **Applies to** any `fix` / `accept suggestion` row that is **not** tagged
  `nit` (Step 6) **and** whose edit touches executable code / behavior.
- **Obligation (test-first / TDD):** for each such row, in the **same commit** as
  the fix (Step 10):
  1. Write or extend the test that captures the bug **first**.
  2. Run it and **confirm it fails** for the expected reason (red) — proving the
     test actually guards the behavior and isn't a tautology.
  3. Apply the code fix.
  4. Run it again and **confirm it passes** (green).

  The test must fail without the fix and pass with it. Ordering the test first
  is what makes that guarantee real rather than assumed.
- **Explicitly skip** `nit` rows and non-code fixes (docs, comments, prose,
  formatting, config with no behavioral surface). Mirror the `nit` predicate's
  "no effect on correctness, behavior, security, performance, or public API"
  language so the two stay consistent.
- **Sandbox / can't-run fallback:** the test is still written first. If the
  environment can't execute it (e.g. a sandbox that can't launch a browser or a
  service), the red→green confirmation falls back to validating through whatever
  harness is available; **note in the commit/reply** that red/green could not be
  run — rather than skipping the test.
- **Strong-default framing** (not an absolute mandate): "default to adding a
  regression test… unless the change is a `nit` or has no runtime surface." This
  avoids the over-application problem the repo's own `instruction-rule-check`
  guards against, while making test-less code fixes the exception.

### Step 7 — plan-table visibility (manual mode)

In `--manual` mode the single confirmation is the Step 7 `Proceed? [y/N/auto]`
gate, shown once before anything is applied. The regression test is **not** a
separate action needing its own gate — it rides along with the `fix` the user is
already confirming (the same way `consistency` rows ride along with their
originating fix). So there is **no second prompt** for the test.

For visibility, flag rows that will get a regression test in the Step 7 plan
table's existing `Note` column (e.g. `+ regression test`) so a manual-mode user
sees it *before* confirming, not just in the commit. Keep the table schema
unchanged — no new column (that would ripple into report templates and tests for
marginal benefit). The `Nit` column already establishes the precedent of an
informational, non-gating signal. A single `y` confirms the fix and its test
together; `auto` proceeds for both.

### Step 10 — cross-reference

Add a one-line cross-reference in **Step 10 (Commit with Commenter Credit)**
noting that the regression test from Step 8 is committed here (in the same commit
as its fix), keeping the pipeline coherent.

### The predicate (for tests)

Model the decision as `requires_regression_test(action, body, touches_code)`
(exact signature at implementation time) in `tests/pr-comments/conftest.py`,
built on the existing `is_nit(body, action)`:

- `fix` / `accept suggestion`, not a nit, touches code → **True**
- same actions but tagged `nit` → **False**
- same actions but non-code change (`touches_code=False`) → **False**
- `reply` / `decline` / `skip` → **False**

## Files to modify

- `skills/pr-comments/SKILL.md` — Step 8 rule (test-first/TDD) + Step 7
  plan-table `Note` flag + Step 10 cross-reference; bump `metadata.version`
  `1.49 → 1.50`.
- `tests/pr-comments/conftest.py` — add the `requires_regression_test(...)`
  predicate.
- `tests/pr-comments/test_regression_test_gate.py` — new test file.

## Tests (required)

`tests/pr-comments/test_regression_test_gate.py` covering, at minimum:

- non-nit `fix` touching code → required
- non-nit `accept suggestion` touching code → required
- `nit`-tagged `fix` / `accept suggestion` → not required
- non-code `fix` (docs/prose/formatting) → not required
- `reply` / `decline` / `skip` → not required

Run `uv run --with pytest pytest tests/` (lift sandbox if the uv cache errors,
per CLAUDE.md).

## Non-goals

- **Evals** — deferred to a follow-up spec (benchmark refresh is a separate,
  heavier task).
- **A hard commit-blocking gate** — rejected in favor of the strong-default +
  fallback framing, to preserve judgment and avoid over-application.
- Editing the `references/*.md` files — the rule is small enough to live inline
  in Step 8.

## Verification

1. `skills/pr-comments/SKILL.md`: Step 8 contains the regression-test rule
   (scope, test-first/TDD red→green ordering, same-commit obligation,
   `nit`/non-code skip, sandbox fallback, strong-default framing); Step 7 flags
   test-bearing rows in the plan-table `Note` with no extra gate; Step 10 has the
   cross-reference; `metadata.version` is `1.50` (bumped exactly once — check
   `git diff origin/main`).
2. `uv run --with pytest pytest tests/` passes, including the new
   `test_regression_test_gate.py`.
3. Each new test asserts a distinct branch of the predicate (required vs. not).
4. `npx cspell` clean on all changed files.
5. SKILL.md reads coherently end-to-end — the new rule, the Step 7 plan-table
   flag, and the Step 10 cross-ref sit naturally in the existing
   Step 6 → 7 → 8 → 10 pipeline.
