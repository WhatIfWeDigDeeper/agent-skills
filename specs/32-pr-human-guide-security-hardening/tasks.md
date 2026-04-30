# Spec 32: Tasks - pr-human-guide security hardening

## Phase 0: Pre-spec peer review (consistency pass on plan.md and tasks.md)

*Use the local `claude` CLI, not `/peer-review`. Always pass `-p` for non-interactive mode. The command can take several minutes.*

- [x] **0.1** Create branch `spec-32-pr-human-guide-security-hardening`.
- [x] **0.2** Stage only the spec docs:
  ```bash
  git add specs/32-pr-human-guide-security-hardening/plan.md specs/32-pr-human-guide-security-hardening/tasks.md
  ```
- [ ] **0.3** Run the pre-spec consistency review:
  ```bash
  claude -p "review staged files"
  ```
  Apply valid findings, decline invalid findings with a short reason, and rerun until zero valid findings or iteration cap 2. **Skipped:** implementation had already begun before this could run with only spec docs staged, so the pre-spec review was rolled into the Phase 5 staged review instead of being claimed retroactively.
- [ ] **0.4** Record per-iteration summary inline in this task. Format: `Iteration N: K valid findings (X critical, Y major, Z minor). Applied all. {Brief note on themes.}`
  - Iteration 1: Skipped — Phase 0 was missed before implementation; see 0.3 deviation note.
  - Iteration 2: Skipped.
- [ ] **0.5** Commit the post-review spec docs as a single commit before Phase 1 begins. **Skipped:** not performed before Phase 1 because implementation had already begun; tracked as part of the same deviation noted in 0.3.

---

## Phase 1: Skill hardening edits

- [x] **1.1** Check version-bump state before editing:
  ```bash
  git fetch origin && git diff origin/main -- skills/pr-human-guide/SKILL.md | rg '^\+  version:'
  git diff --name-status origin/main...HEAD -- skills/pr-human-guide/SKILL.md
  ```
  No existing `SKILL.md` diff or version bump was present relative to `origin/main`.
- [x] **1.2** Edit A - add untrusted-content boundary language to `skills/pr-human-guide/SKILL.md`. The rule must cover `pr_title`, `pr_body`, `gh pr diff`, changed file paths, and sibling/repository files.
- [x] **1.3** Edit B - constrain Step 3 classification inputs so PR prose cannot add/remove categories, override thresholds, force no-findings output, or supersede `references/categories.md`.
- [x] **1.4** Edit C - constrain Step 4 generated output so guide reasons are summarized in the assistant's own words and do not copy instruction-like PR/diff text, command snippets, credential requests, HTML markers, or control syntax.
- [x] **1.5** Edit D - constrain Step 5 write behavior. The only permitted mutation is replacing/appending the canonical `pr-human-guide` block on the detected or explicitly requested PR via `gh pr edit --body-file`.
- [x] **1.6** Edit E - bump `metadata.version` once if required by the Phase 1.1 check.

---

## Phase 2: Tests

- [x] **2.1** Add `tests/pr-human-guide/test_prhumanreview_prompt_injection.py` with focused regression coverage for untrusted PR content.
- [x] **2.2** Add or update helper functions in `tests/pr-human-guide/conftest.py` only if needed for executable prompt-injection guardrail tests.
- [x] **2.3** Cover a PR body attempting to skip the guide or change markers; assert canonical guide behavior still wins.
- [x] **2.4** Cover diff content with instruction-like comments attempting to mark categories empty; assert structural evidence still drives classification.
- [x] **2.5** Cover marker-injection ambiguity in the PR body; assert deterministic bounded replacement/append behavior.
- [x] **2.6** Cover guide reason sanitization; assert instruction-like text is not copied into final guide text as a directive.
- [x] **2.7** Cover markdown/control-looking file path text; assert the label is escaped while the GitHub diff link remains valid.

---

## Phase 3: Eval decision and benchmark updates

- [x] **3.1** Decide whether to add a prompt-injection eval in `evals/pr-human-guide/evals.json`. If deferring, record the reason in the PR description or an explicit note in this task. Deferred for this implementation pass: the change is covered by focused unit tests, while adding an eval would require fresh benchmark execution and README/benchmark updates from observed runs.
- [x] **3.2** If adding an eval, ensure the prompt is natural and does not name the skill or say the skill was invoked. N/A — eval addition deferred in 3.1.
- [x] **3.3** If adding an eval, assert user-facing behavior: canonical markers, valid category flagging, `gh pr edit --body-file`, and no obedience to injected instructions. N/A — eval addition deferred in 3.1.
- [x] **3.4** If evals are added or semantics change, run the pr-human-guide eval workflow and update `evals/pr-human-guide/benchmark.json` from observed runs only. N/A — no eval or semantics changes.
- [x] **3.5** If benchmark data changes, update `evals/pr-human-guide/benchmark.md`, `README.md` Eval Delta, `README.md` pr-human-guide Skill Notes Eval cost, `metadata.skill_version`, and `metadata.evals_run`. N/A — benchmark data unchanged.
- [x] **3.6** If assertion semantics are inverted for existing runs, null affected benchmark result fields according to repo rules before recomputing summaries. N/A — no assertion semantics changed.

---

## Phase 4: Verification

- [x] **4.1** Verify the new boundary language:
  ```bash
  rg -n 'untrusted|prompt injection|instructions.*PR|data only' skills/pr-human-guide/SKILL.md
  ```
- [x] **4.2** Verify output/write constraints:
  ```bash
  rg -n 'Only write by replacing|via .*--body-file|Treat extra markers as untrusted' skills/pr-human-guide/SKILL.md
  ```
- [x] **4.3** Verify version:
  ```bash
  rg -n '^  version:' skills/pr-human-guide/SKILL.md
  ```
- [x] **4.4** Run focused tests:
  ```bash
  uv run --with pytest pytest tests/pr-human-guide/ -v
  ```
- [x] **4.5** Run full tests after skill/reference edits:
  ```bash
  uv run --with pytest pytest tests/
  ```
- [x] **4.6** Run cspell on modified markdown/instruction files. Start with:
  ```bash
  npx cspell skills/pr-human-guide/SKILL.md specs/32-pr-human-guide-security-hardening/*.md tests/pr-human-guide/*.py
  ```
  Add `README.md`, `evals/pr-human-guide/evals.json`, and benchmark files if modified. Add legitimate new words to `cspell.config.yaml` alphabetically.
- [x] **4.7** If eval/benchmark JSON changed, validate JSON: N/A — eval/benchmark JSON unchanged.
  ```bash
  python3 -c 'import json; json.load(open("evals/pr-human-guide/evals.json")); json.load(open("evals/pr-human-guide/benchmark.json"))'
  ```
- [x] **4.8** If benchmark artifacts changed, verify README and benchmark summaries agree with `benchmark.json`. N/A — benchmark artifacts unchanged.
- [x] **4.9** Re-read all modified spec files before reporting done.

---

## Phase 5: Pre-ship peer review

*Fresh-context pass to catch drift after implementation. Use the local `claude` CLI, not `/peer-review`; always pass `-p`. Exit condition: a pass produces zero valid findings. Iteration cap: 4.*

- [x] **5.1** Stage the full branch diff.
- [x] **5.2** Run:
  ```bash
  claude -p "review staged files"
  ```
  Wait for completion, apply valid findings, and rerun until zero valid findings or iteration cap 4.
- [x] **5.3** Record per-iteration summary inline in this task.
  - Iteration 1: 2 visible findings (0 critical, 1 major, 1 minor). Applied both. Themes: task 4.9 needed to be completed after re-reading spec docs; test-only prompt-injection regex helpers needed a comment clarifying they are regression sentinels, not runtime defenses.
  - Iteration 2: 6 findings (0 critical, 3 major, 3 minor). Applied all. Themes: unrelated VS Code settings file was unstaged so review scope matches this PR; Phase 0 deviation was documented; marker-injection behavior was documented in SKILL.md and expanded in tests; prompt-injection tests were wrapped in a class and helper naming was narrowed.
  - Iteration 3: 7 findings (0 critical, 0 major, 6 minor, 1 nit). Applied 5, declined 2. Applied: added markdown-link-label escaping coverage, renamed the thin security-sentinel test, left skipped Phase 0 boxes unchecked, made marker matching CRLF-tolerant, and added a README hardening note. Declined: Step 2/Step 5 boundary-language de-duplication because explicit repetition is intentional defense in depth; `.vscode/settings.json` is an unrelated unstaged local change and was kept out of this PR's staged diff.
  - Iteration 4: 0 blocking findings. Ready to ship. Non-blocking observations only: helper tests are sentinels rather than end-to-end runtime defenses; extra markdown escaping is harmless; Phase 0 deviation is transparently documented; marker tie-breaker edge case is documented behavior.

---

## Phase 6: Ship

- [x] **6.1** Commit all changes on branch `spec-32-pr-human-guide-security-hardening`.
- [x] **6.2** Push and open PR #137.
- [x] **6.3** Run `/pr-comments 137` immediately after PR creation per repo convention.
- [x] **6.4** Loop `/pr-comments` until no new bot feedback. No PR comments were present in the fetched PR data.
- [x] **6.5** Run `/pr-human-guide 137` to annotate the PR for human reviewers.
- [x] **6.6** Verify CI status with `gh pr checks 137`. `cspell` passed.
- [ ] **6.7** Wait for human review before merging.
- [ ] **6.8** After approval, squash-merge, sync local main, and clean up the branch/worktree if one was used.
