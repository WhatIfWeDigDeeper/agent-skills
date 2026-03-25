# Spec 08: pr-comments — Cross-File Consistency Review

## Problem

When pr-comments implements a reviewer's suggestion in one file, it may create inconsistencies with other files in the PR that weren't commented on. Example: a reviewer says "rename `tmp` to `filteredResults`" in `api.ts`, but `handler.ts` (also in the PR diff) uses the same `tmp` variable in the same pattern — no comment there, so the skill ignores it. The result is a half-applied rename that gets pushed without anyone noticing.

CI catches build failures after push, but not stylistic or logical inconsistencies that compile fine. The skill currently has no mechanism to detect this, and no acknowledgement that CI is the backstop for build-breaking changes.

## Proposed Change

Add a new **Step 6b — Cross-File Consistency Check** between Step 6 (Decide) and Step 7 (Present Plan). After classifying all review comments but before presenting the plan, the skill scans other PR-modified files for identifiers that overlap with planned changes. Matches are surfaced as `consistency` rows in the plan table for user confirmation.

Also add a note to the Notes section about CI and validation.

## Detailed Behavior

### Step 6b — Cross-File Consistency Check

After Step 6 completes (all comments classified), before Step 7 (plan presentation):

1. **Extract key identifiers from planned changes.** For each `fix` or `accept suggestion` item, identify the concrete things being changed:
   - Variable, function, class, or constant renames
   - Pattern changes (e.g., error handling style, API call conventions)
   - String literal or config key updates
   - Type/interface signature changes

   Focus on identifiers that appear verbatim in code — not abstract concepts. If a comment says "add a null check before calling `user.name`", the identifier is `user.name`. If it says "rename `tmp` to `filteredResults`", the identifiers are `tmp` (old) and the rename pattern.

2. **Search PR-modified files.** Using the PR diff already fetched in Step 4, search other files in the diff for occurrences of the same identifiers. Scope is strictly limited to files changed in the PR — do not search the entire repository. This is a PR review tool, not a refactoring tool.

   For each match, check whether the surrounding context is analogous (same usage pattern, not just a coincidental name collision). A `tmp` variable in a completely different context doesn't warrant a consistency flag.

3. **Add `consistency` rows to the plan.** For each genuine match, add a new row to the plan table:

   ```
   | # | File | Summary | Action | Note |
   |---|------|---------|--------|------|
   | 1 | src/api.ts:42 | Rename `tmp` to `filteredResults` | `fix` | |
   | 2 | src/handler.ts:18 | Same `tmp` usage as #1 | `consistency` | Apply matching rename? |
   ```

   The Note column should reference the originating item number and briefly describe the proposed parallel change.

4. **No matches? No rows.** If no cross-file consistency issues are found, skip silently — don't add a "no consistency issues found" message. The plan table in Step 7 simply won't have any `consistency` rows.

### Step 7 — Plan Table (updated)

Add `consistency` to the action values list:

- `consistency` — a change inferred from another planned item's implementation, not directly requested by a reviewer. Surfaced for user confirmation.

### Auto-Mode Interaction

`consistency` items are **never auto-approved**, even in `--auto` mode. They weren't requested by a reviewer, so auto-approving them would be overstepping. If any `consistency` items exist in an auto-mode iteration, drop to manual confirmation for that iteration (same behavior as security flags and diff-validation declines).

### Commit Grouping (Step 10)

`consistency` changes are included in the same commit as the originating comment's changes. Credit goes to the original commenter — their suggestion triggered the parallel change. No separate `Co-authored-by` entry is needed for the consistency item since it derives from the same reviewer's feedback.

### Steps 11–12

`consistency` items have no associated review thread. Skip them in:
- Step 11 (Reply to Comments) — nothing to reply to
- Step 12 (Resolve Addressed Threads) — no thread to resolve

### Analysis Constraints

- **Lightweight**: Identifier matching in the diff, not deep semantic analysis or AST parsing. The skill is a text-processing workflow, not a compiler.
- **No cascading**: A consistency fix does not trigger further consistency checks on itself. One pass only.
- **False positives are acceptable**: The user confirms everything in Step 7. A few extra rows that get skipped are better than missing a real inconsistency.
- **False negatives are acceptable**: This is best-effort. Complex cross-file dependencies that require deep understanding will be missed — that's what CI and human review are for.

### CI / Validation Note (new)

Add to the Notes section:

> **Post-implementation validation**: This skill does not run CI, tests, or linting after implementing changes. CI runs after push and catches build failures. The consistency check (Step 6b) reduces but does not eliminate the chance of pushing inconsistent code. For pre-commit validation, configure git pre-commit hooks or assistant-specific hooks (e.g., Claude Code hooks).

## Invariants (unchanged)

- Security screening (Step 5) still runs on all comment text
- `decline` items still get reply explanations
- Co-author credit rules unchanged
- Re-request list logic unchanged
- Bot polling unchanged
- Auto-loop behavior unchanged (except `consistency` forces manual confirmation)

## Skill Changes

Single file: `skills/pr-comments/SKILL.md`

Changes:
- **New Step 6b**: cross-file consistency check (between Steps 6 and 7)
- **Step 7**: add `consistency` to action values; note that it forces manual confirmation in auto-mode
- **Step 10**: note that consistency changes are grouped with their originating comment's commit
- **Notes**: add CI/validation note
- **Version**: 1.8 → 1.9

## New Evals

**Eval 20 — Cross-file consistency: matching rename**
Prompt: PR renames a helper function `getData` to `fetchData` in `src/api.ts` (reviewer comment). `src/routes.ts` (also in PR diff) calls `getData` in the same import/usage pattern but has no review comment. The skill should flag the `routes.ts` usage as a `consistency` item in the plan.

Assertions:
- `src/routes.ts` appears in the plan table with action `consistency`
- The consistency row references the originating `fix` item
- The consistency item is not auto-approved even if `--auto` is active

**Eval 21 — Cross-file consistency: no false positive on unrelated usage**
Prompt: PR fixes a bug in `src/parser.ts` where a variable `result` is renamed to `parsedOutput` (reviewer comment). `src/logger.ts` (also in PR diff) has a variable named `result` but in a completely different context (logging output). The skill should NOT flag the `logger.ts` usage as a consistency item.

Assertions:
- `src/logger.ts` does NOT appear as a `consistency` row in the plan
- Only the original `fix` item appears in the plan for the rename

## Out of Scope

- Searching files outside the PR diff for consistency (that's a repo-wide refactor concern)
- Deep semantic analysis or AST parsing
- Running CI, tests, or linting as part of the skill workflow
- Auto-approving consistency items

## Tasks

See `tasks.md`.
