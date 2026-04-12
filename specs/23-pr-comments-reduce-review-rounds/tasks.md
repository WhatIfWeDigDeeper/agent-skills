# Spec 23: Tasks — pr-comments drift re-scan + convention sanity-check

## Phase 1: SKILL.md Changes

- [x] **1.1** Verify the current version in `skills/pr-comments/SKILL.md` frontmatter is `"1.27"` before making any changes (run `rg '^  version:' skills/pr-comments/SKILL.md`)
- [x] **1.2** Insert new **Step 9** between "8. Apply Changes" and "10. Commit" with the post-edit drift re-scan logic:
  - Collect replaced substrings from Step 8 edits (≥20 chars, or CLI flag/command, or file-path/URL)
  - Search PR-modified files (Step 4 diff) for occurrences of the replaced substrings
  - Detect skill/spec/eval repo structure and apply sibling-artifact pair checks
  - Add `consistency` rows for genuine matches; silent on clean
  - Fold drift fixes into the Step 10 commit with originating reviewer credit
- [x] **1.3** Update the Step 8 "skip" instruction: change "skip the commit and proceed directly to Step 11" to "skip Steps 9 and 10 and proceed directly to Step 11"
- [x] **1.4** Add the **convention-rule sanity-check** to Step 6 — after the "For regular comments:" paragraph, add a new block "**For comments proposing new rules in instructions files:**" covering:
  - Trigger: target file matches `*CLAUDE*.md` or `*instructions*.md`, comment body contains normative language ("must", "always", "convention requires", "should always", etc.)
  - 3-step process: extract claim → grep counter-examples → decide (0–1: `fix` normally; ≥2: soften to `fix` with note or `decline`)
- [x] **1.5** Update Step 7's auto-mode confirmation escalation rule: the current text "or `consistency` items from Step 6b" triggers a pause; update it to clarify that only Step 6b `consistency` rows trigger this pause — Step 9 drift rows do not require confirmation and are applied automatically
- [x] **1.6** Update the Notes section: replace "The consistency check (Step 6b) reduces but does not eliminate the chance of pushing inconsistent code" with the updated two-step (6b + 9) wording from plan.md
- [x] **1.7** Bump `metadata.version` from `"1.27"` to `"1.28"`

---

## Phase 2: Tests

- [x] **2.1** Decide whether new tests belong in `tests/pr-comments/test_consistency_check.py` (alongside existing Step 6b tests) or in a new file `tests/pr-comments/test_post_edit_drift.py` — check `test_consistency_check.py` for existing patterns
  - Decision: two new files — `test_post_edit_drift.py` (Step 9) and `test_convention_sanity_check.py` (Step 6 sanity-check)
- [x] **2.2** Add post-edit drift re-scan tests:
  - `test_trivial_substring_excluded` — short/common substrings not flagged
  - `test_cli_flag_drift_detected` — replaced CLI flag appearing in sibling file is flagged
  - `test_no_drift_silent` — no sibling references → no rows added
- [x] **2.3** Add convention sanity-check tests:
  - `test_convention_file_target_detected` — CLAUDE.md target + "must" language triggers counter-example check
  - `test_counter_examples_found_soften` — ≥2 counter-examples → `fix` with softened wording
  - `test_counter_examples_found_decline` — ≥2 counter-examples, unsoftenable → `decline`
  - `test_no_counter_examples_fix_unchanged` — 0 counter-examples → `fix` unchanged
- [x] **2.4** Run `uv run --with pytest pytest tests/pr-comments/` — all tests pass (270 passed)

---

## Phase 3: Evals (optional but recommended)

- [x] **3.1** Check whether existing `evals/pr-comments/evals.json` has any eval covering post-edit drift or convention-rule adoption: none found
- [x] **3.2** Add eval 37 (post-edit-drift-scan): SKILL.md `--body` → `--body-file` fix with stale plan.md in PR diff; 4 assertions
- [x] **3.3** Add eval 38 (convention-sanity-check): Copilot proposes "all test files must be skill-prefixed" on CLAUDE.md; 4 assertions
- [x] **3.4** Run evals immediately — eval 37: 4/4 with / 3/4 without (+25% discriminating); eval 38: 4/4 / 4/4 (non-discriminating, noted). Updated benchmark.json and benchmark.md

---

## Phase 4: Cspell + Consistency Check

- [ ] **4.1** Run `npx cspell skills/pr-comments/SKILL.md` — add any new unknown words to `cspell.config.yaml` (alphabetically sorted)
- [ ] **4.2** Re-read `SKILL.md` end-to-end — verify Step 9 integrates cleanly with the existing step numbering and that all cross-references to "Step 9" or "Step 10" are correct
- [ ] **4.3** Re-read both `plan.md` and `tasks.md` end-to-end — verify consistency between the two files
- [ ] **4.4** Run `git diff origin/main -- skills/pr-comments/SKILL.md | rg '^\+  version:'` — confirm exactly one version bump exists in the diff

---

## Phase 5: Verification

- [ ] **5.1** Run `uv run --with pytest pytest tests/` — no regressions across all skill test suites
- [ ] **5.2** Invoke `/pr-comments` on a real or synthetic PR where a prior commit changed SKILL.md prose and left a sibling plan.md referencing the old phrasing — confirm Step 9 flags it **and** the fix is included in the same commit as the originating reviewer fix (not a separate commit)
- [ ] **5.3** Invoke `/pr-comments` on a real or synthetic PR where a Copilot comment proposes a universal rule on CLAUDE.md with ≥2 counter-examples in the repo — confirm the classification is softened or declined
