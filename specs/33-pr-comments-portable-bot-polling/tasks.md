# Spec 33: Tasks — pr-comments portable bot polling outside Claude Code

## Phase 0: Pre-spec peer review

- [x] **0.1** Create branch `spec-33-pr-comments-portable-bot-polling`.
- [x] **0.2** Stage only the spec docs:
  ```bash
  git add specs/33-pr-comments-portable-bot-polling/plan.md specs/33-pr-comments-portable-bot-polling/tasks.md
  ```
- [x] **0.3** Run `/peer-review staged files`. Apply valid findings, decline invalid findings with a short reason, and rerun until zero valid findings or iteration cap 2. **Skipped:** implementation had already begun before this could run against a spec-only staged diff, so the first staged review was handled later instead of being claimed retroactively as Phase 0.
- [x] **0.4** Record per-iteration summary inline in this task. Format: `Iteration N: K valid findings (X critical, Y major, Z minor). Applied all. {Brief note on themes.}`
  - Iteration 1: Skipped — Phase 0 was missed before implementation; see 0.3 deviation note.
  - Iteration 2: Skipped.
- [x] **0.5** Commit the post-review spec docs as a single commit before Phase 1 begins. **Skipped:** not performed before Phase 1 because implementation had already begun; tracked as part of the same deviation noted in 0.3.

---

## Phase 1: Skill reference edits

- [x] **1.1** Check version-bump state before editing:
  ```bash
  git fetch origin && git diff origin/main -- skills/pr-comments/SKILL.md | rg '^\+  version:'
  git diff --name-status origin/main...HEAD -- skills/pr-comments/SKILL.md
  ```
- [x] **1.2** Edit A — in `skills/pr-comments/references/bot-polling.md`, update `Poll interval and timeout` to prefer the host runtime's delayed-resume or scheduler primitive when available.
- [x] **1.3** Edit A — add the second fallback: if no scheduler exists but blocking waits are allowed, use the existing bounded `sleep 60` loop and keep the 10-minute timeout.
- [x] **1.4** Edit A — add the third fallback: if neither scheduler nor blocking waits are available, run one immediate Signals 1-3 check, report pending bot review, tell the user to re-invoke `pr-comments` when the review lands, then proceed to Step 14/end the invocation.
- [x] **1.5** Edit A — keep the Claude Code `ScheduleWakeup` call as an example only, and keep the warning not to use `Monitor` for waits of 60 seconds or longer.
- [x] **1.6** Edit B — re-read the updated polling section and confirm the change preserves the existing Signals 1-3 priority, loop-back behavior on new threads, all-bots-responded clean exit, and timeout behavior.
- [x] **1.7** Edit C — bump `metadata.version` in `skills/pr-comments/SKILL.md` once if required by the Phase 1.1 check.

---

## Phase 2: Tests, evals, and benchmark decision

- [x] **2.1** Decide whether any unit test is needed. Expected decision confirmed: no test change, because this is runtime instruction text and `tests/pr-comments/test_bot_poll_routing.py` already covers routing/exit logic.
- [x] **2.2** If helper logic is introduced, add focused tests under `tests/pr-comments/` with a unique basename. N/A — no helper logic was introduced.
- [x] **2.3** Decide whether eval assertions need changes. Expected decision confirmed: no eval change, because existing assertions already cover the intended polling behavior and the new fallback is host-runtime-specific.
- [x] **2.4** If eval assertions change, re-run affected evals from observed transcripts and update benchmark artifacts according to repo rules. N/A — eval assertions did not change.
- [x] **2.5** Confirm historical `evals/pr-comments/benchmark.json` evidence mentioning `sleep 60` remains untouched unless observed run data is actually regenerated. Confirmed — no benchmark files were modified.

---

## Phase 3: Verification

- [x] **3.1** Confirm fallback language:
  ```bash
  rg -n 'delayed-resume|blocking waits|neither.*scheduler|immediate signal check|ScheduleWakeup' skills/pr-comments/references/bot-polling.md
  ```
- [x] **3.2** Confirm version:
  ```bash
  rg -n '^  version:' skills/pr-comments/SKILL.md
  ```
- [x] **3.3** Run focused tests:
  ```bash
  uv run --with pytest pytest tests/pr-comments/ -v
  ```
- [x] **3.4** Run full tests after the skill reference edit:
  ```bash
  uv run --with pytest pytest tests/
  ```
- [x] **3.5** Run cspell on modified markdown/instruction files:
  ```bash
  npx cspell skills/pr-comments/references/bot-polling.md skills/pr-comments/SKILL.md specs/33-pr-comments-portable-bot-polling/*.md
  ```
  Add legitimate new words to `cspell.config.yaml` in alphabetical order if needed.
- [x] **3.6** If eval/benchmark JSON changed, validate JSON: N/A — eval and benchmark JSON files were unchanged.
  ```bash
  python3 -c 'import json; json.load(open("evals/pr-comments/evals.json")); json.load(open("evals/pr-comments/benchmark.json"))'
  ```
- [x] **3.7** If benchmark artifacts changed, verify README and benchmark summaries agree with `benchmark.json`. N/A — benchmark artifacts were unchanged.
- [x] **3.8** Re-read all modified spec files before reporting done.

---

## Phase 4: Pre-ship peer review

*Fresh-context pass to catch drift after implementation. Exit condition: a pass produces zero valid findings. Iteration cap: 4.*

- [x] **4.1** Stage the full branch diff.
- [x] **4.2** Run `/peer-review staged files`, apply valid findings, and rerun until zero valid findings or iteration cap 4.
- [x] **4.3** Record per-iteration summary inline in this task.
  - Iteration 1: NO FINDINGS. Exit condition met.

---

## Phase 5: Ship

- [ ] **5.1** Commit all changes on branch `spec-33-pr-comments-portable-bot-polling`.
- [ ] **5.2** Push and open a PR with `Closes #138` in the PR body.
- [ ] **5.3** Run `/pr-comments {pr_number}` immediately after PR creation per project convention.
- [ ] **5.4** Loop `/pr-comments` until no new bot feedback.
- [ ] **5.5** Run `/pr-human-guide {pr_number}` to annotate the PR for human reviewers.
- [ ] **5.6** Verify CI status with `gh pr checks {pr_number}`.
- [ ] **5.7** Wait for human review before merging.
- [ ] **5.8** After approval, squash-merge, sync local main, and clean up the branch/worktree if one was used.
- [ ] **5.9** Verify issue #138 is closed after merge; close it manually if the PR did not auto-close it.
