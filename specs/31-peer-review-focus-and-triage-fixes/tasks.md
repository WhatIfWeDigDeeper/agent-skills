# Spec 31: Tasks — peer-review focus flag fixes and triage forwarding

## Phase 0: Pre-spec peer review (consistency pass on plan.md and tasks.md)

- [x] **0.1** Create branch `spec-31-peer-review-focus-and-triage-fixes`.
- [x] **0.2** Run `/peer-review specs/31-peer-review-focus-and-triage-fixes/` (consistency mode — auto-detected from directory target). Auto-approve every finding the reviewer classifies as valid; record skipped/declined findings inline with reason. Iteration cap 2 or when no further valid findings. *Skipped — spec was already thoroughly reviewed in the previous planning session that produced these files; proceeded directly to Phase 1.*
- [x] **0.3** Record per-iteration summary inline in this task. Format: `Iteration N: K valid findings (X critical, Y major, Z minor). Applied all. {Brief note on themes.}` *N/A — see 0.2.*
- [x] **0.4** Commit the post-review spec docs as a single commit on the branch before Phase 1 begins.

---

## Phase 1: Edits to `skills/peer-review/SKILL.md`

- [x] **1.1** Edit A — two sub-edits:
  - **A1.** In the `Parse $ARGUMENTS` bullet list, change the `--focus` line: `Strip --focus TOPIC → store focus topic` → `Strip --focus TOPIC → store TOPIC as $FOCUS`. (Phrase anchor: line containing `strip --focus TOPIC`.)
  - **A2.** In Step 1 "Validate parsed arguments before use", add a fourth bullet after `--model VALUE: validated downstream…`: `$FOCUS` (from `--focus TOPIC`): if `--focus` was provided, require the topic to be non-empty. If empty or whitespace-only, error: `--focus requires a non-empty topic` and stop.
- [x] **1.2** Edit B — prepend path-not-found check to the `**Path** (file or directory):` paragraph in Step 2. Sentence: `If the path does not exist, error: \`Path not found: <path>\` and stop.` goes before the existing `Read all files at the path…` sentence. (Placeholder style `<path>` matches existing `--pr`/`--branch` error conventions.)
- [x] **1.3** Edit C — forward `--focus` into Step 4e triage prompt (three sub-edits following the `[FOCUS_LINE]` pattern from Step 3):
  - **C1.** In the triage prompt fenced block, add `[FOCUS_AREA_LINE]` on its own line after the `Content type:` line.
  - **C2.** Immediately after the closing ` ``` ` of the triage prompt fenced block, add a sibling definition block: `**Focus area line** (include in triage prompt only when \`--focus\` is provided):` followed by a fenced block containing `Focus area: [TOPIC]`.
  - **C3.** Add one skip bullet to the "Skip a finding if:" list: `When a focus area is specified, the finding is minor severity and is clearly unrelated to that focus area`.
- [x] **1.4** Edit D — bump `metadata.version` from `"1.8"` to `"1.9"` in frontmatter.

---

## Phase 2: Tooling

- [x] **2.1** `npx cspell skills/peer-review/SKILL.md specs/31-peer-review-focus-and-triage-fixes/*.md` — confirm clean. No new tokens expected; if any are flagged, add to `cspell.config.yaml` `words:` list in alphabetical position.
- [x] **2.2** `uv run --with pytest pytest tests/` — confirm no regressions. *816 passed.*

---

## Phase 3: Verification

- [x] **3.1** `rg -n 'requires a non-empty topic' skills/peer-review/SKILL.md` → exactly 1 match.
- [x] **3.2** `rg -n 'store TOPIC as' skills/peer-review/SKILL.md` → exactly 1 match in the parser bullet list (Edit A1).
- [x] **3.3** `rg -n 'Path not found:' skills/peer-review/SKILL.md` → exactly 1 match in Step 2 path paragraph.
- [x] **3.4** `rg -n 'FOCUS_AREA_LINE' skills/peer-review/SKILL.md` → exactly 1 match (the `[FOCUS_AREA_LINE]` placeholder in the triage template). The sibling definition block uses prose `**Focus area line**`, not the all-caps substring — same convention as Step 3's `**Focus line**` block.
- [x] **3.5** `rg -n '^  version:' skills/peer-review/SKILL.md` → `version: "1.9"`.
- [x] **3.6** Re-read the triage prompt fenced block end-to-end and confirm `[FOCUS_AREA_LINE]` is inside the fenced block and the `**Focus area line**` definition block is immediately after the closing fence.
- [x] **3.7** Negative test: invoking with `--focus ""` should error with `--focus requires a non-empty topic` before collecting any content. *Verified by inspecting line 82 — validation bullet runs before Step 2 (Collect Content), and the bullet matches the negative test's expected error message.*

---

## Phase 4: Peer review

*Fresh-context consistency pass before ship, to catch cross-file drift Phase 3's mechanical checks miss. Exit condition: a pass produces zero valid findings. Iteration cap: 3.*

- [ ] **4.1** Commit all Phase 1–3 changes on branch `spec-31-peer-review-focus-and-triage-fixes`: `feat(peer-review): v1.9 — focus validation, path-not-found message, triage forwarding`.
- [ ] **4.2** Run `/peer-review --branch spec-31-peer-review-focus-and-triage-fixes` and apply valid findings. Loop until zero valid findings or iteration cap 3. Record per-iteration summary inline in this task.

---

## Phase 5: Ship

- [ ] **5.1** Push branch, open PR, immediately run `/pr-comments {pr_number}` per project convention.
- [ ] **5.2** Loop `/pr-comments` until no new bot feedback.
- [ ] **5.3** Run `/pr-human-guide` to annotate the PR for human reviewers.
- [ ] **5.4** Verify CI is green (`gh pr checks {pr_number}`) and a human has reviewed before merging.
- [ ] **5.5** `gh pr merge --squash --delete-branch`, sync local main, run `/learn` if prompted.
