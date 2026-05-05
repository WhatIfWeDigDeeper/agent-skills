# Spec 35: Tasks — pr-comments bot re-request hardening and `@file` harness fallback

## Phase 0: Pre-spec peer review

- [x] **0.1** Create branch `spec-35-pr-comments-bot-rerequest-and-fallbacks`.
- [x] **0.2** Stage only the spec docs:
  ```bash
  git add specs/35-pr-comments-bot-rerequest-and-fallbacks/plan.md specs/35-pr-comments-bot-rerequest-and-fallbacks/tasks.md
  ```
- [x] **0.3** Run `/peer-review staged files`. Apply valid findings, decline invalid findings with a short reason, and rerun until zero valid findings or iteration cap 2.
- [x] **0.4** Record per-iteration summary inline in this task. Format: `Iteration N: K valid findings (X critical, Y major, Z minor). Applied all. {Brief note on themes.}`
  - Iteration 1: 8 valid findings (1 critical, 4 major, 3 minor). Applied all. Themes: timestamp variable contradiction in B1, hardcoded `/tmp/` path in C, B3 placement underspecified, Risks-section caveats not reflected in B1 step content, plus minor verification-regex and re-read drift.
  - Iteration 2: 3 valid findings (0 critical, 1 major, 2 minor). Applied all. Themes: case-sensitive `verify.*event` regex would false-clean against the planned `**Verify` wording; tasks.md missed the all-zero `bot_reviewers` fall-through to Step 14; "~5 seconds" / "5-second" inconsistency.
- [x] **0.5** Commit the post-review spec docs as a single commit before Phase 1 begins.

---

## Phase 1: Skill text edits

- [x] **1.1** Check version-bump state before editing:
  ```bash
  git fetch origin && git diff origin/main -- skills/pr-comments/SKILL.md | rg '^\+  version:'
  git diff --name-status origin/main...HEAD -- skills/pr-comments/SKILL.md
  ```
- [x] **1.2** Edit A (issue #141) — in `skills/pr-comments/SKILL.md` Step 13b, replace the "Bot reviewers" sentence with the proposed wording in `plan.md` → "Edit A". Verify the existing anchors `gh pr edit`, `requestReviewsByLogin`, and the REST handoff are preserved.
- [x] **1.3** Edit B1 (issue #144) — in `skills/pr-comments/references/bot-polling.md`, insert a new step 4 in the `Entry from Step 13b` section between the POST step (current 3) and "Proceed to the Shared polling loop" (current 4). Renumber existing step 4 → step 5. Match the design in `plan.md` → "Edit B1". The new step must reuse the existing `snapshot_timestamp` (recorded in step 1 before the POST) — do not introduce a new timestamp variable. The step content must include the caveats from `plan.md` → "Risks": (a) the 5-second sleep is heuristic and may produce false negatives on slow/delayed emissions, with the UI-fallback as a safe backstop; (b) on harnesses where `sleep` is blocked the event check runs immediately; (c) the gate counts any post-snapshot `review_requested` event without per-login filtering (the events API login form often differs from the canonical `bot_reviewers` form, so a per-bot predicate would false-negative). If the total `event_count` is 0, surface the UI-fallback message for every bot and empty `bot_reviewers`; otherwise leave `bot_reviewers` unchanged and proceed to the Shared polling loop. If `bot_reviewers` ends up empty, skip the Shared polling loop entirely and proceed to Step 14.
- [x] **1.4** Edit B1 — verify the renumbering: search the file for any `step 4` / `step 5` cross-references in the same section and any cross-section references; update them if pointing at the renumbered targets.
- [x] **1.5** Edit B2 (issue #144) — append the "Known limitations: silent no-op POST for re-reviewed bots" subsection at the end of `references/bot-polling.md`, after "Bot Display Names". Match the design in `plan.md` → "Edit B2".
- [x] **1.6** Edit B3 (issue #144) — in `skills/pr-comments/SKILL.md` Step 13b, insert the new verification pointer as a **new item 3** in the existing "After the POST:" numbered list (between current items 2 and 3), pushing the existing item 3 ("Resume the shared bot-polling flow…") to item 4. Use the wording from `plan.md` → "Edit B3".
- [x] **1.7** Edit C (issue #145) — append "Harness denies `@file` reference" section to `skills/pr-comments/references/error-handling.md`. Match the design in `plan.md` → "Edit C".
- [x] **1.8** Edit D — bump `metadata.version` in `skills/pr-comments/SKILL.md` from `"1.39"` to `"1.40"`, only if the Phase 1.1 check shows no existing bump on the branch.

---

## Phase 2: Tests, evals, and benchmark decision

- [x] **2.1** Decide whether any unit test is needed. Expected decision: no test change, because the three edits are documentation/agent-instruction text and the runtime check (event verification) requires a real GitHub PR to exercise.
- [x] **2.2** If executable helper logic is introduced, add focused tests under `tests/pr-comments/` with a unique basename. N/A unless implementation deviates.
- [x] **2.3** Decide whether eval assertions need changes. Expected decision: no eval change, because existing assertions cover Step 13b routing at a behavioral level and the new gate is a runtime check.
- [x] **2.4** If eval assertions change, re-run affected evals from observed transcripts and update benchmark artifacts according to repo rules. N/A unless implementation deviates.
- [x] **2.5** Confirm historical `evals/pr-comments/benchmark.json` evidence is unchanged. No benchmark file should be modified.

---

## Phase 3: Verification

- [x] **3.1** Confirm Edit A anchors and new wording:
  ```bash
  rg -n 'requestReviewsByLogin|silently no-op|Never use .gh pr edit. for any bot' skills/pr-comments/SKILL.md
  ```
- [x] **3.2** Confirm Edit B1 verification step and Edit B3 SKILL.md pointer (use simple anchors rather than a single ordering-sensitive regex):
  ```bash
  rg -n 'review_requested' skills/pr-comments/SKILL.md skills/pr-comments/references/bot-polling.md
  rg -ni 'verify.*event' skills/pr-comments/SKILL.md
  rg -n 'Entry from Step 13b' skills/pr-comments/SKILL.md
  ```
- [x] **3.3** Confirm Edit B2 "Known limitations" subsection:
  ```bash
  rg -n 'Known limitations: silent no-op POST' skills/pr-comments/references/bot-polling.md
  ```
- [x] **3.4** Confirm Edit C `@file` fallback section:
  ```bash
  rg -n 'Harness denies .@file. reference' skills/pr-comments/references/error-handling.md
  ```
- [x] **3.5** Confirm Edit D version bump:
  ```bash
  rg -n '^  version:' skills/pr-comments/SKILL.md
  ```
- [x] **3.6** Run focused tests:
  ```bash
  uv run --with pytest pytest tests/pr-comments/ -v
  ```
- [x] **3.7** Run full tests:
  ```bash
  uv run --with pytest pytest tests/
  ```
- [x] **3.8** Run cspell on modified markdown/instruction files:
  ```bash
  npx cspell skills/pr-comments/SKILL.md skills/pr-comments/references/bot-polling.md skills/pr-comments/references/error-handling.md specs/35-pr-comments-bot-rerequest-and-fallbacks/*.md
  ```
  Add legitimate new words to `cspell.config.yaml` in alphabetical order if needed.
- [x] **3.9** If eval/benchmark JSON changed (it should not), validate JSON:
  ```bash
  python3 -c 'import json; json.load(open("evals/pr-comments/evals.json")); json.load(open("evals/pr-comments/benchmark.json"))'
  ```
- [x] **3.10** Re-read all modified spec and skill files before reporting done. Re-read both `plan.md` and `tasks.md` end-to-end after final edits. Re-read both SKILL.md Step 13b and `bot-polling.md` "Entry from Step 13b" end-to-end and verify cross-references are consistent.

---

## Phase 4: Pre-ship peer review

*Fresh-context pass to catch drift after implementation. Exit condition: a pass produces zero valid findings. Iteration cap: 4.*

- [x] **4.1** Stage the full branch diff.
- [x] **4.2** Run `/peer-review staged files`, apply valid findings, and rerun until zero valid findings or iteration cap 4.
- [x] **4.3** Record per-iteration summary inline in this task.
  - Iteration 1: NO FINDINGS. Exit condition met.
  - Iteration 2: N/A (exited at iteration 1).
  - Iteration 3: N/A.
  - Iteration 4: N/A.

---

## Phase 5: Ship

- [x] **5.1** Commit all changes on branch `spec-35-pr-comments-bot-rerequest-and-fallbacks`.
- [x] **5.2** Push and open a PR with `Closes #141`, `Closes #144`, `Closes #145` in the PR body. → PR #147
- [x] **5.3** Run `/pr-comments {pr_number}` immediately after PR creation per project convention.
- [x] **5.4** Loop `/pr-comments` until no new bot feedback.
- [ ] **5.5** Run `/pr-human-guide {pr_number}` to annotate the PR for human reviewers.
- [ ] **5.6** Verify CI status with `gh pr checks {pr_number}`.
- [ ] **5.7** Wait for human review before merging.
- [ ] **5.8** After approval, squash-merge, sync local main, and clean up the branch/worktree if one was used.
- [ ] **5.9** Verify issues #141, #144, #145 are closed after merge; close any not auto-closed.
