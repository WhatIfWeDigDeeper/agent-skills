# Consistency Scans

Two related scan procedures: the **Cross-File Consistency Check** (Step 6b, before the plan is presented) and the **Post-edit Drift Re-scan** (Step 9, after edits are applied). Both find places where a planned or applied change leaves a sibling occurrence behind. Execute the section named by the calling step.

## Step 6b — Cross-File Consistency Check

After Step 6 (all comments classified), before presenting the plan in Step 7, scan other PR-modified files for identifiers that overlap with planned changes.

1. **Extract key identifiers from planned changes.** For each `fix` or `accept suggestion` item, identify the concrete things being changed:
   - Variable, function, class, or constant renames
   - Pattern changes (e.g. error-handling style, API call conventions)
   - String literal or config key updates
   - Type/interface signature changes

   Focus on identifiers that appear verbatim in code — not abstract concepts. "Rename `getData` to `fetchData`" → identifier is `getData` (old name). "Add a null check before `user.name`" → identifier is `user.name`.

2. **Search PR-modified files.** Using the PR diff fetched in Step 4, search other files in the diff for the same identifiers. Scope is strictly the PR-changed files — do not search the whole repository. For each match, check whether the surrounding context is analogous (same usage pattern, not a coincidental name collision). A `result` in a logging context is not a match for a `result` being renamed in a parser context.

3. **Add `consistency` rows to the plan.** For each genuine match, add a row whose Note column references the originating item number and briefly describes the proposed parallel change:

   ```
   | # | File | Summary | Action | Note |
   |---|------|---------|--------|------|
   | 1 | src/api.ts:42 | Rename `getData` to `fetchData` | `fix` | |
   | 2 | src/routes.ts:18 | Same `getData` usage as #1 | `consistency` | Apply matching rename? |
   ```

4. **No matches? No rows.** Skip silently — do not add a "no consistency issues found" message.

**Constraints:** lightweight identifier matching in the diff only (no AST/semantic analysis), one pass (no cascading), false positives/negatives acceptable — CI and human review catch what this misses. Step 6b `consistency` rows always require explicit confirmation in Step 7, even in auto mode.

## Step 9 — Post-edit Drift Re-scan

After all Step 8 edits are applied, before committing, scan for stale sibling references introduced by those edits. This catches a fix that changes a command, flag, or phrasing in one file but leaves the same text in related artifacts (reference files, specs, benchmark evidence, README rows).

1. **Collect replaced substrings.** From every file edited in Step 8, identify the non-trivial substrings that were replaced. Non-trivial means ≥20 characters, or a CLI flag (e.g. `--body-file`), or a file-path/URL literal. Skip pure whitespace, single-word tweaks, and numeric-only changes.

2. **Search PR-modified files by default.** Using the diff fetched in Step 4, search each PR file for those replaced substrings. Default scope is PR-modified files — do not search the whole repository, except for the sibling-artifact checks in item 3.

3. **Special-case: skill/spec/eval repo structure.** When the PR diff contains any path matching `skills/*/SKILL.md`, `evals/*/evals.json`, or `specs/*/plan.md`, also check these sibling-artifact pairs **even when those siblings are not in the PR diff** — an intentional expansion beyond item 2's scope. (Adjust the `skills/` prefix to match your repo's skill directory structure — e.g. `.agents/skills/` if that is where skills live):

   | Canonical file changed | Sibling artifacts to check |
   |------------------------|---------------------------|
   | `skills/<name>/SKILL.md` | `skills/<name>/references/*.md`, `specs/*-<name>/plan.md`, `specs/*-<name>/tasks.md`, `evals/<name>/benchmark.json` `evidence` fields, `README.md` skill row |
   | `evals/<name>/evals.json` assertion `text` | `evals/<name>/benchmark.json` expectation `text` fields |
   | `specs/*-<name>/plan.md` | `specs/*-<name>/tasks.md` (and vice versa) |

4. **Add `consistency` rows and fix immediately.** For each genuine match (the old substring appears in a sibling file in the same sense — not coincidental), add a `consistency` row and apply the fix in the same pass. Include it in the Step 10 commit with the originating reviewer's credit. Step 9 drift rows are **auto-applied without confirmation** — they are mechanical corrections, not judgment calls, and do not trigger the Step 7 auto-mode escalation that Step 6b rows do. If Step 9 adds any rows, emit an updated drift summary before Step 10 listing those new `consistency` rows and their files so the user sees the final committed change set; this is a disclosure, not a new approval gate.

5. **No matches → no rows.** If Step 9 finds nothing, do not emit any extra Step 9 summary.

Step 11 and Step 12 skip both Step 6b and Step 9 `consistency` rows (no thread to reply to or resolve).
