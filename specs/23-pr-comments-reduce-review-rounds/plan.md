# Spec 23: pr-comments — Reduce Review Iterations (Drift Re-scan + Convention Sanity-Check)

## Problem

Analysis of PR #101 (`feat/pr-human-guide`) showed two distinct sources of avoidable Copilot review iterations:

1. **Post-fix prose/command drift** — when a fix changes a command or phrasing in a canonical file (e.g., SKILL.md migrating from `--body` to `--body-file`), sibling artifacts that reference the same command are not updated in the same commit. Those stale copies surface as new Copilot findings in subsequent rounds. The existing Step 6b consistency check runs *before* edits using planned-change identifiers, so it can't see drift that is about to be introduced by the edits themselves.

2. **Flawed universal-rule adoption** — when a reviewer (e.g., Copilot) suggests adding a new mandatory convention rule to an instructions file (CLAUDE.md, copilot-instructions.md), the rule is adopted without verifying whether it actually holds across the existing codebase. If the claim is wrong (e.g., "all test files must be skill-prefixed" but `tests/js-deps/test_*.py` and `tests/pr-comments/test_*.py` already contradict it), the next review round flags the newly-added rule as inconsistent. PR #101 generated two extra rounds — and 5 declined rename suggestions — from this pattern.

The two patterns together were responsible for ~6 of ~31 Copilot findings (19%) and several avoidable review rounds.

## Design

### Change 1: Step 9 — Post-edit Drift Re-scan

A new step between "Apply Changes" (Step 8) and "Commit" (Step 10). After all planned edits are applied in Step 8, before committing:

1. **Collect replaced substrings.** From every file edited in Step 8, identify the non-trivial substrings that were replaced. "Non-trivial" means: ≥20 characters, or a CLI flag/command name, or a file-path/URL literal. Exclude pure whitespace changes, single-word tweaks, and numeric-only changes.

2. **Search PR-modified files.** Using the diff already fetched in Step 4, search each file that appears in the PR for occurrences of those replaced substrings. Scope: PR-modified files only (same constraint as Step 6b).

3. **Special-case: skill/spec/eval repo structure.** When the PR is in a repo structured like this one, also check these known sibling-artifact pairs even if the file wasn't otherwise flagged:

   | Canonical file changed | Sibling artifacts to check |
   |------------------------|---------------------------|
   | `skills/<name>/SKILL.md` | `skills/<name>/references/*.md`, `specs/*-<name>/plan.md`, `specs/*-<name>/tasks.md`, `evals/<name>/benchmark.json` `evidence` fields, `README.md` skill row |
   | `evals/<name>/evals.json` assertion `text` | `evals/<name>/benchmark.json` expectation `text` fields |
   | `specs/*-<name>/plan.md` | `specs/*-<name>/tasks.md` (and vice versa) |

   Detection: check if the PR diff contains any path matching `skills/*/SKILL.md`, `evals/*/evals.json`, or `specs/*/plan.md`.

4. **Add `consistency` rows to the plan.** For each genuine match (the old substring appears in a sibling file in the same sense — not a coincidental occurrence), add a `consistency` row. Include the fix in the Step 10 commit with the originating reviewer's credit. Step 9 drift rows are **auto-applied without confirmation** (even in auto mode) — they are mechanical corrections with no judgment involved, unlike Step 6b consistency rows which pause auto mode for confirmation. Step 7's confirmation escalation rule for `consistency` items continues to apply only to Step 6b rows, not Step 9 rows. Step 11 and Step 12 skip Step 9 rows (no thread to reply to or resolve), same as Step 6b rows.

5. **No matches → no rows.** Silent on clean.

**Rationale for post-edit placement:** Running before Step 10 (commit) means drift fixes land in the same commit as the reviewer fix that caused them — one push, one review round.

### Change 2: Step 6 Convention Sanity-Check

An addition to Step 6 classification logic. When a review comment:
- targets a file that is an instructions or conventions file (`CLAUDE.md`, `.github/copilot-instructions.md`, `AGENTS.md`, any file matching `*instructions*.md` or `*CLAUDE*.md`)
- proposes adding or strengthening a rule using normative language ("must", "always", "convention requires", "convention is", "should always", "all … must", "all … should")

Then, before finalizing the `fix` classification, the skill must:

1. **Extract the empirical claim** the proposed rule makes (e.g., "all test files must have skill-prefixed basenames").

2. **Grep for counter-examples.** Search the full local repo checkout (not limited to PR diff) for patterns that violate the claim:
   ```bash
   # Example: proposed rule "all test files must be prefixed test_<skillname>_"
   # Counter-example search: test files NOT matching that prefix in tests/
   find tests -name 'test_*.py' | grep -v 'test_[a-z]*_[a-z]' | head -5
   ```
   The specific search depends on the claim; use judgment to form an appropriate grep/find.

3. **Decision:**
   - **0–1 counter-examples:** classify as `fix` normally. The rule is consistent with existing patterns (or the one counter-example is the file being changed).
   - **≥2 counter-examples:** do not classify as `fix` outright. Instead:
     - If the suggestion can be softened to a *preference* rather than a mandate (add "prefer" / "when in doubt" / "to avoid collision"), reclassify as `fix` with the softened wording and note the counter-examples in the reply.
     - If softening would remove the point of the suggestion, classify as `decline` with a reply explaining the counter-examples (e.g., "Existing suites `tests/js-deps/` and `tests/pr-comments/` use un-prefixed names — adopting this as a mandatory rule would require renaming them and would still be inconsistent with the existing layout").

**Scope:** Only applies to suggestions targeting instruction/convention files. Does not apply to code-level suggestions or documentation other than these convention files.

## Workflow Changes

### SKILL.md changes

1. **New Step 9** (inserted between "8. Apply Changes" and "10. Commit"):
   - Title: `### 9. Post-edit Drift Re-scan`
   - Content: rules described in Change 1 above.
   - Step 9 `consistency` rows: folded into the Step 10 commit, credited to the originating reviewer, no thread to reply to or resolve (same as Step 6b), but **not** subject to the Step 7 auto-mode confirmation escalation that Step 6b rows trigger.

2. **Step 6 augmentation** — add a new sub-bullet under the classification rules (after the "For regular comments:" paragraph):
   - Title: **Convention-rule sanity-check** (or a header like "**For comments proposing new rules in instructions files:**")
   - Content: the 3-step process described in Change 2 above.

3. **Step 8 skip instruction** — update the existing sentence "skip the commit and proceed directly to Step 11" (the no-edits early-exit in Step 8) to read "skip Steps 9 and 10 and proceed directly to Step 11" (Step 9 must also be skipped when Step 8 made no edits — there's nothing to scan).

4. **Version bump** — `metadata.version: "1.27"` → `"1.28"`.

### Notes section change

Replace the existing Post-implementation validation note:

> *The consistency check (Step 6b) reduces but does not eliminate the chance of pushing inconsistent code.*

with:

> *Step 6b (pre-edit) and Step 9 (post-edit) together cover planned-change propagation and prose/command drift. Neither step substitutes for CI, tests, or linting.*

## Step 6 Terminal Output

The plan table already shows `consistency` rows — no change needed to the Step 7 template. Step 9 drift rows use the same table schema as Step 6b rows.

## Tests

Add to `tests/pr-comments/test_consistency_check.py` (or a new file `test_post_edit_drift.py`):

- `test_trivial_substring_excluded` — substrings under 20 chars that are common words are not flagged
- `test_cli_flag_drift_detected` — a replaced CLI flag (`--body` → `--body-file`) appearing in a sibling file is flagged
- `test_no_drift_silent` — when no sibling references the replaced substring, no rows are added
- `test_convention_file_target_detected` — comment targeting CLAUDE.md with "must" language triggers counter-example check
- `test_counter_examples_found_soften` — ≥2 counter-examples → classification becomes `fix` with softened wording
- `test_counter_examples_found_decline` — ≥2 counter-examples, unsoftenable → `decline`
- `test_no_counter_examples_fix_unchanged` — 0 counter-examples → `fix` classification unchanged

## Verification

1. Run `uv run --with pytest pytest tests/pr-comments/` — all existing tests pass, new tests pass.
2. Manually invoke `/pr-comments` on a PR where a prior commit changed SKILL.md prose and left a sibling `plan.md` referencing the old phrasing — confirm Step 9 flags it and folds the fix into the same commit.
3. Manually invoke `/pr-comments` on a PR where a review comment proposes "all X must be Y" targeting CLAUDE.md, and the repo already has counter-examples (e.g., `rg -l 'test_' tests/` returns files not matching the proposed naming rule) — confirm the suggestion is reclassified as softened `fix` or `decline` with counter-example evidence in the reply.
4. Run `npx cspell skills/pr-comments/SKILL.md` — no new unknown words.
