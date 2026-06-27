# Spec 46: Tasks — pr-comments eval-driven review-and-improve pass

Tracks issue
[#196](https://github.com/WhatIfWeDigDeeper/agent-skills/issues/196). Check off
each item as it completes — do not batch at the end.

## Phase 0: Baseline & re-verification

- [ ] **0.1** Re-verify current state (it drifts): `rg '^  version:'
  skills/pr-comments/SKILL.md`, `wc -l skills/pr-comments/SKILL.md`,
  `git log --oneline -3 -- skills/pr-comments/`. Confirm version is still v1.46
  (or note the new value) and reconcile the step numbers cited in `plan.md`
  against the current SKILL.md.
- [ ] **0.2** Confirm benchmark baseline directly from `benchmark.json` run
  entries (not `benchmark.md` prose): record current `skill_version` (expect
  1.36), Opus with/without means (expect 0.9887 / 0.5986), and the 9
  non-discriminating Opus eval IDs (expect 5, 6, 24, 27, 29, 32, 33, 35, 38).
- [ ] **0.3** Snapshot the current skill (`skills/pr-comments/`) into a temp
  baseline dir for the without-skill arm of the Phase 4 eval re-run. Record the
  exact version snapshotted.
- [ ] **0.4** Read `tests/pr-comments/test_push_rerequest_routing.py`,
  `test_stale_head_ordering.py`, `test_pr_argument_parsing.py`, and
  `test_prcomments_argument_validation.py` — note which exact wordings/branches
  the Phase 1 and Phase 2 edits must preserve.

---

## Phase 1: Area 1 — Trim Step 13 redundancy

- [ ] **1.1** In SKILL.md "### 13. Push and Re-request Review", add a single
  labeled **stale-HEAD invariant** block near the top stating once: the pre-push
  commenter list is never final; stale-HEAD bots (incl. clean-approval-only) are
  detected and merged at step 2 after any push; prompts/status-lines name the
  detection step and drop the `from @user…` clause when the list is empty.
- [ ] **1.2** Collapse the per-variant restatements (lead-in paragraph, "Do not
  finalize the reviewer list" paragraph, manual-prompt paragraph, auto
  status-line paragraph, no-commit variant, empty-list variant, numbered step-2
  paragraph) to the bare template/instruction + a pointer to the invariant.
- [ ] **1.3** Decide and document whether to move the prompt/status-line
  templates (manual prompt, auto status line, no-commit + empty-list variants)
  into `references/bot-polling.md` behind an imperative handoff, or collapse them
  in place. If moved: use fenced ` ```text ` blocks with the "fences are markdown
  only" instruction (per `skills/CLAUDE.md`), and name the target section + what
  not to re-run in the handoff sentence.
- [ ] **1.4** Re-run the Phase 0.4 test files — all still pass. Adjust any test
  whose asserted wording legitimately changed (and note why in the commit).

---

## Phase 2: Area 2 — Finish Arguments dedup

- [ ] **2.1** Confirm `references/argument-parsing.md` still holds the full
  `--auto`/`--max` deprecation + `--auto 42` ambiguity detail (it does as of
  v1.46) — this area is mostly complete; scope is small.
- [ ] **2.2** Evaluate the SKILL.md disambiguation **table row** `| `/pr-comments
  --auto 42` | auto | 42 … |`: drop it or reduce to a one-line pointer to the
  reference's "`--auto` + PR-number disambiguation" section — **only if** no test
  in `test_pr_argument_parsing.py` / `test_prcomments_argument_validation.py`
  depends on it. If a test depends on it, leave the row and record that here.
- [ ] **2.3** Run the argument-parsing tests — all pass.

---

## Phase 3: Area 3 — Hunt logic gaps

- [ ] **3.1** For each candidate (a–e in `plan.md`), read the current SKILL.md +
  references and classify as **intentional exclusion** or **genuine miss**.
  Record the verdict + evidence for each in this file (and post the findings as a
  comment on #196).
  - [ ] (a) edited/updated comment bodies across runs
  - [ ] (b) reaction-only feedback
  - [ ] (c) resolved-then-reopened threads
  - [ ] (d) comments on the PR description/body itself
  - [ ] (e) human comments arriving mid-run (Step 6c repoll bot-only)
- [ ] **3.2** For each **intentional exclusion** not already documented, add one
  line to SKILL.md "## Notes" (or the relevant step) stating the boundary. No
  behavioral change.
- [ ] **3.3** For each **genuine miss**, scope a minimal fix (e.g. (a): re-open a
  previously-handled thread when comment `updated_at` is newer than the latest
  author/operator reply; (e): widen the repoll to all comment sources, or
  document as an accepted limitation if a full fix risks loops). If a fix is
  large/risky, document the limitation and defer to a follow-up issue instead of
  over-building.
- [ ] **3.4** Add a new test in `tests/pr-comments/` for each genuine-miss fix
  that lands. Add a new eval to `evals/pr-comments/evals.json` if the fix
  warrants one.

---

## Phase 4: Area 4 — Refresh benchmark

- [ ] **4.1** Re-run all 38 evals — with_skill (current skill) vs the Phase 0.3
  snapshot baseline — on Opus 4.7 executor / Sonnet 4.6 analyzer (to stay
  comparable with the recorded run); grade and aggregate per `evals/CLAUDE.md`.
- [ ] **4.2** Re-evaluate the 9 non-discriminating evals (5, 6, 24, 27, 29, 32,
  33, 35, 38): for each, leave as-is / strengthen assertions / note why it stays
  non-discriminating. Record decisions in `benchmark.md`.
- [ ] **4.3** Update `benchmark.json` to the new `skill_version`, run entries,
  `run_summary`, and `run_summary_by_model`. Rewrite via `json.dump(...,
  ensure_ascii=True)` to preserve `\uXXXX` escapes (root CLAUDE.md note).
- [ ] **4.4** Update `benchmark.md` prose to match the new data (problem-statement
  framing, rates, non-discriminating-eval notes).

---

## Phase 5: Version, security, docs

- [ ] **5.1** Bump `metadata.version` in SKILL.md exactly once. First run
  `git fetch origin && git diff origin/main -- skills/pr-comments/SKILL.md |
  rg '^\+  version:'` to confirm no bump already exists on the branch.
- [ ] **5.2** Update the `README.md` pr-comments row **only if** behavior changed.
- [ ] **5.3** If any ingestion path changed (Steps 2/2b/2c/6), refresh the
  security baseline: `bash evals/security/scan.sh --update-baselines --confirm`,
  commit `evals/security/pr-comments.baseline.json`. Otherwise skip.

---

## Phase 6: Cspell + consistency

- [ ] **6.1** `npx cspell skills/pr-comments/SKILL.md
  skills/pr-comments/references/*.md specs/46-pr-comments-eval-driven-review/*.md`
  — add new words to `cspell.config.yaml` (alphabetically sorted); remove any
  entry no longer used.
- [ ] **6.2** Re-read SKILL.md end-to-end — Step 13 invariant stated once,
  prompts/status-lines reference it, no dangling cross-references, step numbering
  intact.
- [ ] **6.3** Re-read `plan.md` and `tasks.md` end-to-end — verify the two files
  are consistent with each other and with the edits actually made.

---

## Phase 7: Verification

- [ ] **7.1** `uv run --with pytest pytest tests/pr-comments/` — all pass.
- [ ] **7.2** `uv run --with pytest pytest tests/` — no regressions (lift sandbox
  restrictions for the uv cache; in Claude Code `dangerouslyDisableSandbox:
  true`).
- [ ] **7.3** Confirm benchmark: with_skill mean ≥ recorded v1.36 baseline
  (0.9887 Opus); no eval regresses below its prior with_skill rate without an
  explained cause.
- [ ] **7.4** `git fetch origin && git diff origin/main --
  skills/pr-comments/SKILL.md | rg '^\+  version:'` — exactly one bump.
