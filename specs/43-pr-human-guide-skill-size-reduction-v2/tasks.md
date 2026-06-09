# Spec 43: Tasks — pr-human-guide extract shell/gh calls to a new reference file

## Phase 1: Pre-implementation baseline

- [x] **1.1** Confirm work is on branch `spec-43-pr-human-guide-skill-size-reduction-v2` (branched off clean `main` after PR #178 merged).
- [x] **1.2** Check version-bump state (once-per-PR rule):
  ```bash
  git fetch origin && git diff origin/main -- skills/pr-human-guide/SKILL.md | rg '^\+  version:'
  git diff --name-status origin/main...HEAD -- skills/pr-human-guide/SKILL.md
  ```
  Expected: no prior bump; status `M` → bump required (0.12→0.13).
- [x] **1.3** Record starting line count: `wc -l skills/pr-human-guide/SKILL.md` → 270.

> **Phase 1 results:** On branch `spec-43-…` off clean `main`. Starting count 270 lines, v0.12. No prior bump (M, not A) → bump to 0.13 required.

---

## Phase 2: Skill edits

*Use phrase anchors, not line numbers.*

- [x] **2.1** Create `skills/pr-human-guide/references/commands.md` with the file-writing tool (not shell). Three sections holding the Step 1 / Step 2 / Step 5 shell **verbatim** from the current SKILL.md, each with an intro paragraph; mirror `output-format.md`'s intro style.
- [x] **2.2** Slim **Step 1**: keep the help-flag check, the `^[1-9][0-9]{0,5}$` validation prose, and the `Invalid PR number:` error; replace both bash blocks + explanatory paragraphs with one "**you must now execute … Fetch PR identity and repo**" delegation naming the populated variables.
- [x] **2.3** Slim **Step 2**: replace the two `gh pr diff` commands with a "**you must now execute … Gather the diff**" delegation; keep the "store separately" sentence.
- [x] **2.4** Slim **Step 5**: keep the replace/append intro, the inline `<!--`→`<\!--` zsh rationale summary, and the passive `marker-helper.py` pointer; delegate the bash to "**you must now execute … Write the guide into the PR body**".
- [x] **2.5** Bump `metadata.version` `"0.12"` → `"0.13"`.
- [x] **2.6** Re-read SKILL.md end-to-end: workflow reads coherently, every `commands.md` handoff imperative, no step assumes content removed from an earlier step.

> **Phase 2 results:** `commands.md` created (3 sections). Steps 1/2/5 slimmed to imperative delegations; step numbering preserved 1–6. Version → 0.13. SKILL.md now 178 lines.

---

## Phase 3: Verification

- [x] **3.1** Line count: `wc -l skills/pr-human-guide/SKILL.md` → **178** (< 200 ✓).
- [x] **3.2** Byte-identity: extract code fences from `commands.md`, confirm each appears verbatim in `git show HEAD:skills/pr-human-guide/SKILL.md`. Result: all 5 relocated blocks byte-identical; the 6th original block (`<untrusted_pr_content>`) correctly remains inline.
- [x] **3.3** Delegations imperative: `rg -n 'references/commands.md' skills/pr-human-guide/SKILL.md` → 3 matches, each "**you must now execute …**".
- [x] **3.4** Security model + untrusted block still inline: `rg -n '^## Security model|untrusted_pr_content' skills/pr-human-guide/SKILL.md`.
- [x] **3.5** `uv run --with pytest pytest tests/pr-human-guide/` → 135 passed (no test matched a relocated string).
- [x] **3.6** `uv run --with pytest pytest tests/` → 1136 passed.
- [x] **3.7** `bash evals/security/scan.sh` → exit 0; pr-human-guide baseline 1 / scanned 1 (W011 still fires, no regression, no baseline edit).
- [x] **3.8** `npx cspell …` → 5 files checked, 0 issues.
- [x] **3.9** Re-read SKILL.md, `commands.md`, and both spec files end-to-end. Post-iteration-1 re-verify: 178 lines (<200 ✓), 135 pr-human-guide tests pass, cspell 0 issues across 5 files, security scan exit 0 (pr-human-guide baseline 1 / scanned 1, no regression).

> **Phase 3 results:** 178 lines (< 200 ✓). All 5 relocated code fences byte-identical to original; `<untrusted_pr_content>` stays inline. 3 imperative `commands.md` delegations. Tests 135 + 1136 passed. Security scan exit 0, W011 unchanged. cspell clean.

---

## Phase 4: skill-creator review loop (≤3 iterations)

*Spawn a subagent invoking `/skill-creator` to review the refactored skill. I triage findings; implement only valid ones (reject anything conflicting with byte-identical relocation, the mandatory-step delegation pattern, the <200-line goal, or the W011 security framing). Re-run the review after any change. Stop on a clean pass or after 3 iterations. Re-run verification 3.1/3.5–3.6 after any file-changing iteration.*

- [x] **4.1** Iteration 1 — spawn subagent, triage, apply valid findings. `Iteration 1: 5 findings (applied 3 / declined 2). Applied: removed duplicate "Store the full diff…" sentence from SKILL.md Step 2 delegation (kept in commands.md); added a "Run after Step 1…" when/why lead-in to commands.md Gather-the-diff section; expanded the bare marker-helper.py prose citation to the full repo-root path. Declined: hardcoded "Steps 1, 2, and 5" in commands.md intro (numbering is a frozen constraint, mirrors output-format.md convention); .number rationale appearing in both SKILL.md and commands.md (intentional explain-the-why at both altitudes — reviewer concurred).` Re-ran verification: 178 lines (<200 ✓), 135 + (full suite) tests pass.
- [x] **4.2** Iteration 2 (4.1 changed files) — re-ran the subagent review on the updated SKILL.md + commands.md. `Iteration 2: CLEAN, 0 findings.` Verified all reference links resolve, all three commands.md handoffs name an existing section with imperative phrasing and name what they produce, no cross-altitude contradictions, 178 lines (<200). Clean pass → loop terminates (2 of 3 iterations used).
- [x] **4.3** Iteration 3 — not needed (4.2 was a clean pass with no file changes).

---

## Phase 5: Ship

- [x] **5.1** Update `README.md` Eval-cost note with the v0.13 entry.
- [x] **5.2** Commit on branch `spec-43-pr-human-guide-skill-size-reduction-v2` (commit `caffac5`).
- [x] **5.3** Push and open the PR → #180.
- [x] **5.4** Run `/pr-comments {pr_number}` immediately after PR creation; loop until no new bot feedback. `Both bots reviewed PR #180 clean: Copilot reviewed 5/5 files with no comments (skip); claude[bot] timeline comment "No issues found. Checked for bugs and CLAUDE.md compliance." (clean approval). Zero actionable inline/review-body/timeline comments. Loop terminated.`
- [x] **5.5** Run `/pr-human-guide {pr_number}` before human review. `Added a no-areas guide block to PR #180 (all changes are documentation: skill markdown relocation, spec docs, README note — Selectivity Threshold docs exception). Markers posted correctly, no behavior change.`
- [x] **5.6** Verify CI green with `gh pr checks {pr_number}`. `cspell pass, security-scan pass, exit 0.`
- [x] **5.7** Wait for human review before merging. `PR #180 is at the awaiting-human-review gate: both bots clean, CI green, human guide posted. Will not merge until a human reviews — bot approval alone is not a substitute.`
