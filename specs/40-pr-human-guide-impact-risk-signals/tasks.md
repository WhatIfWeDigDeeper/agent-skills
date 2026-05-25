# Spec 40: Tasks - pr-human-guide Impact Risk signals (augment existing categories)

## Phase 0: Pre-spec peer review (consistency pass on plan.md and tasks.md)

*Use the local `claude` CLI, not `/peer-review`. Always pass `-p` for non-interactive mode. The command can take several minutes.*

- [x] **0.1** Create branch `spec-40-pr-human-guide-impact-risk-signals`.
- [x] **0.2** Stage only the spec docs:
  ```bash
  git add specs/40-pr-human-guide-impact-risk-signals/plan.md specs/40-pr-human-guide-impact-risk-signals/tasks.md
  ```
- [x] **0.3** Run the pre-spec consistency review:
  ```bash
  claude -p "review staged files"
  ```
  Apply valid findings, decline invalid findings with a short reason, and rerun until zero valid findings or iteration cap 2. Reached iteration cap 2 with substantive findings applied in both iterations; remaining residue (if any) will surface in Phase 5 pre-ship review which has a higher cap.
- [x] **0.4** Record per-iteration summary inline in this task. Format: `Iteration N: K valid findings (X critical, Y major, Z minor). Applied all. {Brief note on themes.}`
  - Iteration 1: 4 valid findings (0 critical, 2 major, 2 minor). Applied all. Themes: plan/tasks sync for Edit B and Edit C wording (Findings 1 and 3); grammatical fix for Edit A's first replacement using "impact risk" rather than bare "impact" (Finding 2); acknowledgement that the new Novel Patterns bullet style (bold-label) is intentional to give the signals named handles (Finding 4).
  - Iteration 2: 5 valid findings (1 critical, 2 major, 2 minor). Applied all. Themes: Edit B's "codemod-style rename" example contradicted Edit C's guardrail — replaced with behavior/contract-delta examples (framework migration, API surface change, logging/error-handling pattern swap) and made the "no semantic delta" exclusion explicit in both bullets (Finding 1, critical); added a rationale paragraph to Edit B and a Context paragraph acknowledging that Section 5's framing is being stretched from novelty to aggregate scope (Finding 2); added a concrete trigger heuristic to the high-fanout signal — path-prefix matches plus 5+ same-diff importers — so detection cost is operationally bounded (Finding 3); specified that Edit D appends to the first paragraph of Selectivity Threshold, not the Exceptions list (Finding 4); added verification item 12 to plan.md to sync with tasks.md 4.12 (Finding 5); refreshed the recommended fixtures in the Evals section to match the revised Edit B examples.
- [x] **0.5** Commit the post-review spec docs as a single commit before Phase 1 begins.

---

## Phase 1: Skill edits (categories.md + version bump)

- [x] **1.1** Check version-bump state before editing:
  ```bash
  git fetch origin && git diff origin/main -- skills/pr-human-guide/SKILL.md | rg '^\+  version:'
  git diff --name-status origin/main...HEAD -- skills/pr-human-guide/SKILL.md
  ```
  Result: no prior bump on branch, no diff vs origin/main. Edit E (version bump) is required.
- [x] **1.2** Edit A — terminology refresh in `skills/pr-human-guide/references/categories.md`:
  - Section **2. Config / Infrastructure** rationale: replace `"a blast radius that isn't visible from the diff alone"` with `"impact risk that isn't visible from the diff alone"` (threads the new term through the prose; "have impact" alone is ungrammatical).
  - Section **4. Data Model Changes** "What does NOT qualify": replace `"low blast radius"` with `"low impact risk"`.
- [x] **1.3** Edit B — under **5. Novel Patterns** "Examples of novel patterns that qualify", add two new bullets (verbatim from plan.md Edit B):
  - **Sweeping cross-cutting refactor** — a transformation applied across many files at once where the change carries a behavior or contract delta (e.g., a framework migration across an entire module, an API surface change propagated to 20+ call sites, swapping a logging or error-handling pattern in a way that changes runtime behavior). Flag for the aggregate decision, not each file; the question for the reviewer is "is this the right transformation," not "is each line correct." Pure-mechanical renames with no semantic delta do **not** qualify — see Edit C.
  - **High-fanout core helper edits** — non-trivial behavior changes to a module that is imported broadly across the codebase (root router, base controller, shared error helper, central middleware chain). **Trigger sampling** when (a) the changed file's path matches a typically-shared layout (`router`, `controller`, `middleware`, base error/exception classes, `lib/*`, `util/*`, `common/*`) **or** (b) the changed export name appears as an import in 5+ other files within the same PR diff; otherwise skip sampling. When sampling fires, read 2–3 importers and check whether the changed function/export is called from many call sites.
- [x] **1.4** Edit C — under the same section's "What does NOT qualify" list, add one bullet (verbatim from plan.md Edit C):
  - Pure mechanical changes with no behavior delta (auto-formatting, whitespace-only diffs, dependency-version bumps in lockfiles, single-token renames where the new name is exhaustively substituted) — count as routine even when they touch many files.
- [x] **1.5** Edit D — under **Selectivity Threshold**, append one sentence to the **first paragraph** (the one ending in *"…flag only when there is a concrete reviewer-relevant risk or uncertainty."* — not the "Exceptions" list that follows): *File count alone is not a flagging signal — flag a sweeping change only when the reviewer has a meaningful yes/no decision to make about the transformation as a whole.*
- [x] **1.6** Edit E — bump `metadata.version` in `skills/pr-human-guide/SKILL.md` from `"0.9"` to `"0.10"` (only if 1.1 confirmed no prior bump on the branch).

---

## Phase 2: Tests

- [x] **2.1** No new tests in this spec — confirm by reviewing the existing `tests/pr-human-guide/` suite to ensure no existing test encodes the old "blast radius" wording or relies on the unchanged category text.
  ```bash
  rg -n 'blast radius' tests/pr-human-guide/
  ```
  Result expected: no matches. Confirmed — no matches.
- [x] **2.2** Run the focused suite as a regression check:
  ```bash
  uv run --with pytest pytest tests/pr-human-guide/ -v
  ```
  Result: 135 passed in 0.05s.

---

## Phase 3: Eval decision and benchmark updates

- [x] **3.1** Decide and document: no new eval is added in this spec; no existing eval is re-run. The existing 8-eval suite does not exercise the new signals, so re-benchmarking would not produce informative signal.
- [x] **3.2** Add a single note to `evals/pr-human-guide/benchmark.md` (near the existing "Known Eval Limitations" section): note added as the first subsection of "Known Eval Limitations", titled `### v0.10 — Impact Risk signals (spec 40)`.
- [x] **3.3** Do not change `metadata.skill_version`, `metadata.evals_run`, or any `runs[]` entries in `benchmark.json` — the existing convention is that `skill_version` reflects the version under which recorded runs were produced (v0.7), not the current skill version.
- [x] **3.4** Do not change `README.md` Eval Δ or Skill Notes Eval cost — no benchmark numbers change.

---

## Phase 4: Verification

- [x] **4.1** Verify no "blast radius" remains in skill content:
  ```bash
  rg -n 'blast radius' skills/pr-human-guide/
  ```
  Expected: no matches. Confirmed.
- [x] **4.2** Verify the terminology refresh landed:
  ```bash
  rg -n 'impact risk|impact that isn'"'"'t' skills/pr-human-guide/references/categories.md
  ```
  Expected: two matches. Confirmed (lines 40, 123).
- [x] **4.3** Verify the two new Novel Patterns bullets:
  ```bash
  rg -n 'Sweeping cross-cutting refactor|High-fanout core helper' skills/pr-human-guide/references/categories.md
  ```
  Expected: two matches. Confirmed (lines 158, 166).
- [x] **4.4** Verify the new "does NOT qualify" guardrail:
  ```bash
  rg -n 'Pure mechanical changes' skills/pr-human-guide/references/categories.md
  ```
  (Anchor shortened from the original "Pure mechanical changes with no behavior delta" — the longer phrase wraps across a line break in the source and `rg` does not match across newlines by default.)
  Expected: two matches (Phase 5 iteration 1 harmonized the Edit B cross-reference wording to match the exclusion bullet verbatim). Confirmed at lines 164 and 182.
- [x] **4.5** Verify the Selectivity Threshold sentence:
  ```bash
  rg -n 'File count' skills/pr-human-guide/references/categories.md
  ```
  (Anchor shortened from the original "File count alone is not a flagging signal" — the longer phrase wraps across a line break.)
  Expected: one match. Confirmed at line 233.
- [x] **4.6** Verify the version bump (or its absence per 1.1):
  ```bash
  rg -n '^  version:' skills/pr-human-guide/SKILL.md
  ```
  Expected: `version: "0.10"`. Confirmed.
- [x] **4.7** Verify the benchmark.md note:
  ```bash
  rg -n 'v0.10 — Impact Risk signals' evals/pr-human-guide/benchmark.md
  ```
  Expected: one match. Confirmed at line 56.
- [x] **4.8** Run focused tests:
  ```bash
  uv run --with pytest pytest tests/pr-human-guide/ -v
  ```
  Result: 135 passed in 0.05s.
- [x] **4.9** Run full tests:
  ```bash
  uv run --with pytest pytest tests/
  ```
  Result: 1136 passed in 1.45s.
- [x] **4.10** Run cspell:
  ```bash
  npx cspell skills/pr-human-guide/references/categories.md skills/pr-human-guide/SKILL.md evals/pr-human-guide/benchmark.md specs/40-pr-human-guide-impact-risk-signals/*.md
  ```
  Added `codemod` and `fanout` to `cspell.config.yaml` in alphabetical position. Final cspell result: Files checked: 5, Issues found: 0.
- [x] **4.11** Spot-check: skim `categories.md` end-to-end to confirm tone and selectivity remain consistent — no contradiction between the new sweeping-refactor signal and the existing "What does NOT qualify" lists in other categories. Section 5 framing extension (lines 132–135) bridges novelty and aggregate-scope coherently; the new "Pure mechanical changes" guardrail in the "What does NOT qualify" block (lines 179–182) is consistent with Edit C and the section-level message remains tight.
- [x] **4.12** Re-read all modified spec files (`plan.md`, `tasks.md`) before reporting done. Done.

---

## Phase 5: Pre-ship peer review

*Fresh-context pass to catch drift after implementation. Use the local `claude` CLI, not `/peer-review`; always pass `-p`. Exit condition: a pass produces zero valid findings. Iteration cap: 4.*

- [ ] **5.1** Stage the full branch diff.
- [ ] **5.2** Run:
  ```bash
  claude -p "review staged files"
  ```
  Wait for completion, apply valid findings, and rerun until zero valid findings or iteration cap 4.
- [ ] **5.3** Record per-iteration summary inline in this task.
  - Iteration 1: _pending_
  - Iteration 2: _pending_
  - Iteration 3: _pending_
  - Iteration 4: _pending_

---

## Phase 6: Ship

- [ ] **6.1** Commit all changes on branch `spec-40-pr-human-guide-impact-risk-signals`.
- [ ] **6.2** Push and open the PR. Record PR number inline once known.
- [ ] **6.3** Run `/pr-comments {pr_number}` immediately after PR creation per repo convention.
- [ ] **6.4** Loop `/pr-comments` until no new bot feedback.
- [ ] **6.5** Run `/pr-human-guide {pr_number}` to annotate the PR for human reviewers.
- [ ] **6.6** Verify CI status with `gh pr checks {pr_number}`. All checks must pass (or report `"no checks reported"`).
- [ ] **6.7** Wait for human review before merging.
- [ ] **6.8** After approval, squash-merge with `gh pr merge --squash --delete-branch`, sync local main with `git status --porcelain` → (stash if dirty) → `git reset --hard origin/main` → (pop if stashed), and clean up the branch/worktree if one was used.
