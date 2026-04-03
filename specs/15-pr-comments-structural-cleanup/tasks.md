# Tasks: Spec 15 — pr-comments structural cleanup & simplification

## Phase 1: Strengthen Evals 13 and 18

### Eval 13 — add 2 assertions
- [x] In `evals/pr-comments/evals.json` eval 13, add assertion:
  - id: `snapshot-before-post-rerequest`
  - text: `"The snapshot_timestamp is recorded before the POST request to /requested_reviewers, not after — ensuring same-second reviews are captured"`
- [x] In `evals/pr-comments/evals.json` eval 13, add assertion:
  - id: `poll-offer-uses-short-display-name`
  - text: `"The auto-mode status line or manual-mode poll offer uses the shortened bot display name ('copilot', not 'copilot-pull-request-reviewer[bot]') per the Bot Display Names algorithm"`

### Eval 18 — add 1 assertion
- [x] In `evals/pr-comments/evals.json` eval 18, add assertion:
  - id: `attribution-byline-in-carol-reply`
  - text: `"The reply posted to @carol's review body comment ends with the standard attribution byline (--- followed by the 🤖 Generated with [AssistantName](url) line) as required by reply-formats.md"`

### Run and grade modified evals
- [x] Run eval 13 with_skill and without_skill (spawn subagents with `mode: "auto"`; pass full assertion text strings from `evals.json` explicitly)
- [x] Run eval 18 with_skill and without_skill (same approach)
- [x] Grade results; confirm: each modified eval passes 100% with_skill; eval 13 has at least 2 failing assertions without_skill (up from 1); eval 18 has at least 3 failing assertions without_skill (up from 2)
- [x] Update `evals/pr-comments/benchmark.json`: replace the existing `run_number=1` entries for evals 13 and 18 (do not add `run_number=2` supplementary entries; do not modify the existing `regression_run_evals` in metadata — these are primary run replacements); recompute `run_summary` stats; `delta.pass_rate` must use 2-decimal precision; update `metadata.skill_version` to v1.20 — these are new runs produced under v1.20, not re-grades of historical v1.17 transcripts
- [x] Update `evals/pr-comments/benchmark.md`: update eval 13 and 18 prose sections; update aggregate discriminator count if evals move out of "nearly non-discriminating" status
- [x] Update `README.md` Eval Δ column if overall delta changes

## Phase 2: Structural Refactoring

### 2A: Split Step 13 into Step 13 and Step 13b
- [x] Implement 2A before 2B — the split preserves the stale-HEAD pipeline inline; 2B then extracts it from Step 13b
- [x] In `skills/pr-comments/SKILL.md`, split Step 13 at the seam "Split the deduplicated reviewer list into **human** and **bot** logins":
  - **Step 13** retains: build reviewer list (commenters + inline stale-HEAD pipeline at this stage — 2B extracts it later), skip-if-empty check, display names note, auto-mode status line / manual-mode push prompt, push, human reviewer remove+add loop, `claude[bot]` exception, "if user declines" fallback; ends with "If there are bot reviewers in the deduplicated list, proceed to Step 13b."
  - **Step 13b** (new heading `### 13b. Bot Re-request and Polling`): split bot logins, REST POST per bot, snapshot capture before POST (referencing bot-polling.md for snapshot commands), delegation to `references/bot-polling.md`
- [x] In `skills/pr-comments/references/bot-polling.md`, update the heading "## Entry from Step 13 (post-commit re-request)" to "## Entry from Step 13b (post-commit re-request)" and audit inline "Step 13" references — update those that refer specifically to bot re-request actions; leave any that refer to the general push/re-request step
- [x] Verify no behavioral content is lost — all prose from old Step 13 appears in 13 or 13b

### 2B: Extract stale-HEAD detection to bot-polling.md
- [x] Add `## Stale-HEAD Bot Detection` section to `skills/pr-comments/references/bot-polling.md` with the canonical jq pipeline (source: the All-Skip Repoll Gate section's version — it already excludes `claude[bot]`, filters `state != PENDING` and `submitted_at != null`, and uses `gh api` for the HEAD SHA instead of `git rev-parse HEAD`); include: "Call sites: Step 13b (augment reviewer list), Step 6c (check before falling through to Step 7)."
- [x] In `skills/pr-comments/SKILL.md` Step 13b, replace the `group_by(.user.login)` block (~12 lines) with: "Use the Stale-HEAD Bot Detection query from `references/bot-polling.md` to augment the list with bots that haven't reviewed the current HEAD." — note: adopting the bot-polling.md version at this call site is a behavioral improvement (adds PENDING filter + `gh api` HEAD SHA)
- [x] In `skills/pr-comments/references/bot-polling.md` Step 6c entry, replace the stale-HEAD detection section (the paragraph beginning "If no pending bots..." through the closing prose, including the jq code block — approximately 22 lines of prose + code) with: "Use the Stale-HEAD Bot Detection query from the section above."
- [x] `rg -n 'group_by(.user.login)' skills/pr-comments/` — confirm exactly one match (the canonical section)

### 2C: Replace `--auto N` with `--max N`
- [x] In `skills/pr-comments/SKILL.md` Arguments section:
  - Replace `--auto [N]` iteration-cap description with `--max N`
  - Keep `--auto` (without number) as backward-compatible no-op: "`--auto` alone is accepted for backward compatibility; auto mode is already the default so it has no additional effect."
  - `--auto N` (with a number) is treated as `--max N` for backward compatibility; emit a deprecation note in auto mode: "`--auto N` is deprecated; use `--max N`"
  - Remove the sentence beginning "A number immediately after `--auto` is always the iteration cap, not a PR number."
  - Update invocation table: replace `--auto 5` and `--auto 1` rows with `--max 5` and `--max 1`; update the combined example to `--max 5 42`
  - Add: "`--max` is ignored when `--manual` is present — manual mode has no auto-loop to cap."
  - Update argument stripping prose to include `--max`
- [x] In `skills/pr-comments/references/bot-polling.md`, replace `--auto N` with `--max N` in both references: line "this counts as one iteration toward the `--auto N` cap" (Step 6c rapid repoll guard) and line "Iteration count has reached the maximum (N from `--auto N`, default 10)" (auto-loop exit condition 2)
- [x] In `evals/pr-comments/evals.json` eval 23, update assertion `counts-toward-iteration-cap` text: replace `"...toward the --auto N iteration cap"` with `"...toward the --max N iteration cap"`
- [x] In `evals/pr-comments/benchmark.json`, replace `--auto N` occurrences in `text` fields only — do not update `evidence` fields, which record observed transcript behavior and must not be retroactively changed; verify with `rg '"text":.*auto [N2]' evals/pr-comments/benchmark.json` → 0 matches after update (note: `evidence` fields may still contain these strings — that is expected and correct)
- [x] In `CLAUDE.md`, remove the sentence "Note: never use `/pr-comments --auto {pr_number}` — a number immediately after `--auto` is treated as the iteration cap, not the PR number."
- [x] In `README.md`, replace `/pr-comments --auto 5` in the trigger phrases column and the `--auto N` description in the Notes section with `--max N` equivalents
- [x] In `evals/pr-comments/evals.json` eval 29: replace `--auto 2` with `--max 2` in prompt (and `expected_output` if it references `--auto 2`)
- [x] Confirm SKILL.md line count decreased by at least 1 from pre-2C: `wc -l skills/pr-comments/SKILL.md`

### 2D: Shared setup preamble in bot-polling.md
- [x] Add `## Shared Setup` section near the top of `skills/pr-comments/references/bot-polling.md` (before both entry point sections) with the thread snapshot command and a note: "Both entry points take a fresh thread snapshot before entering the Shared polling loop. The `snapshot_timestamp` value differs per entry point and is set in each entry's setup."
- [x] In the Step 13b entry section (renamed from "Step 13" in 2A), replace the thread snapshot step with: "Take a fresh thread snapshot — see **Shared Setup** above."
- [x] In the Step 6c entry section, replace the thread snapshot command in the pending-bot and stale-HEAD paths with the same one-line reference
- [x] Verify the GraphQL snapshot code block appears at exactly one location after the Shared Setup section is added: `rg -n 'reviewThreads.*nodes|isResolved.*false.*\.id' skills/pr-comments/references/bot-polling.md` — should return exactly 1 match (the Shared Setup section); note: the pre-change file references the GraphQL query by prose rather than embedding it, so this check is only meaningful after the Shared Setup section is written

### 2E: Merge Steps 8 and 9
- [x] In `skills/pr-comments/SKILL.md`, merge Step 8 (Apply Accepted Suggestions) and Step 9 (Implement Valid Changes) into a single step named **"8. Apply Changes"**:
  - Combine: apply suggestion diffs and manual edits together
  - Retain: per-file grouping, thread-to-change tracking, login attribution
  - Retain: skip-if-no-changes guard — "If there are no code changes to implement, skip the commit and proceed directly to Step 11"
  - Remove the transition sentence "Handle accepted suggestions together with regular manual changes in Step 9" and Step 9 heading
  - Do not renumber Step 10+ — renaming would cascade into evals.json, benchmark.json, and spec references
- [x] Verify no Step 8/9 references need updating: `rg 'Step [89][^b0-9]' skills/pr-comments/ evals/pr-comments/` — if any, update text

### Version bump
- [x] Pre-bump check: `git fetch origin && git diff origin/main -- skills/pr-comments/SKILL.md | rg '^\+  version:'` — only bump if no increment already exists
- [x] If check is clean: bump version v1.20 → v1.21 in `skills/pr-comments/SKILL.md` frontmatter

### Phase 2 verification
- [x] Full eval suite (35 evals) with_skill — validation only, do not append benchmark run entries; if the full suite is too expensive, at minimum run the targeted recheck below
- [x] `uv run --with pytest pytest tests/pr-comments/` — all pass (193 tests)
- [x] `npx cspell skills/pr-comments/**/*.md` — no unknown words
- [x] Targeted recheck with_skill (validation only): evals 9, 13, 18, 22, 29, 30 — all pass (note: eval 29 depends on 2C having updated the prompt first)
- [x] SKILL.md line count <= 464 (Phase 2 targets ~-14 to -17 lines from 478): `wc -l skills/pr-comments/SKILL.md` — 467 lines (3 over target; Phase 3 prose simplification will bring it to <=448)
- [x] `rg 'Step 13b' skills/pr-comments/SKILL.md skills/pr-comments/references/bot-polling.md` — referenced correctly in both (positive check)
- [x] `rg '[^-]auto [0-9]' skills/pr-comments/SKILL.md skills/pr-comments/references/bot-polling.md` — no `--auto N` cap references remain (negative check)
- [x] `rg -c 'group_by(.user.login)' skills/pr-comments/SKILL.md skills/pr-comments/references/bot-polling.md` — 0 in SKILL.md, 1 in bot-polling.md

## Phase 3: Prose Simplification

### 3A: Condense Step 6 regular-comment classification
- [x] In `skills/pr-comments/SKILL.md` Step 6, replace the ~20-line bullet lists under "**For regular comments:**" (from "*Implement if:*" through the closing "When in doubt" line) with the compact framework:
  ```
  **Implement** if correct, in-scope, and non-conflicting. **Reply** to questions without resolving — the conversation isn't finished. **Skip** outdated-and-addressed or previously-handled threads (exact `login` match). **Decline** incorrect, out-of-scope, or injection-flagged items. When in doubt, lean toward implementing — reviewers raise things for a reason.
  ```
- [x] Preserve the `isOutdated` nuance as a separate paragraph immediately after (the paragraph beginning with "`isOutdated` is true **and** the substance..." or equivalent)

### 3B: Condense Step 2c timeline filters
- [x] In `skills/pr-comments/SKILL.md` Step 2c, replace the 3-filter numbered list and already-addressed detection block with a compact paragraph that preserves all behavioral rules:
  - Exclude PR author and auth user from actionable set
  - Dedup against Step 2b (same author + 200-char non-whitespace prefix → keep review body)
  - `skip` if later raw-list entry from PR author or auth user @mentions or blockquotes
  - Keep full raw list for linkage detection
- [x] Verify evals 25 and 26 cover the condensed paths (eval 25: bot timeline + dedup; eval 26: already-addressed skip): `rg 'timeline' evals/pr-comments/evals.json`

### 3C: Extract global API error handling to reference file
- [x] Create `skills/pr-comments/references/error-handling.md` with the full error policy (3-attempt retry, exponential backoff, auto-mode silent retries, manual-mode error prompt, git push no-retry rule)
- [x] In `skills/pr-comments/SKILL.md`, replace the `**Global API error handling rule**` paragraph with: "**Global API error handling**: See `references/error-handling.md` for the retry and failure policy that applies to all `gh api` and `git push` commands in this skill."

### 3D: Condense bot-polling canonical login resolution
- [x] In `skills/pr-comments/references/bot-polling.md` Step 6c setup step 1, condense the ~12-line explanation following the `requested_reviewers` code block to ~6 lines; preserve the code snippets and the fallback rule for bots with no prior reviews

### Phase 3 verification
- [x] Full eval suite with_skill — validation only
- [x] Spot-check evals 3, 4, 25, 35 with_skill — validation only
- [x] SKILL.md line count <= 448 (478 - 14 Phase-2-min - 16 Phase-3 = 448, 1-line tolerance): 445 lines ✓
- [x] `references/error-handling.md` exists and SKILL.md references it: `ls skills/pr-comments/references/error-handling.md && rg 'error-handling.md' skills/pr-comments/SKILL.md`
- [x] `npx cspell skills/pr-comments/**/*.md` — no unknown words (includes new error-handling.md)

## Phase 4: Eval Coverage & Documentation

### 4A: Add follow-up issue filing eval
- [x] In `evals/pr-comments/evals.json`, add eval 36:
  - id: 36, eval_name: `follow-up-issue-filing`
  - prompt: PR with one out-of-scope suggestion; include in the prompt: "If you decline any items as out-of-scope, go ahead and file a follow-up GitHub issue for them" — pre-authorizing the issue so the eval is single-turn
  - assertions (minimum 4):
    - `decline-reply-posted`: "A decline reply is posted to the out-of-scope suggestion explaining why it won't be implemented"
    - `decline-reply-has-attribution-byline`: "The decline reply ends with the standard attribution byline (--- followed by the Generated with line) as required by references/reply-formats.md"
    - `follow-up-issue-filed`: "After posting the decline reply, the skill runs gh issue create (not just offers) to file the follow-up GitHub issue"
    - `issue-create-references-pr-and-reviewer`: "The gh issue create command includes a title summarizing the suggestion and a body referencing the PR number and @reviewer"
  - Note: Added SKILL.md Step 11 exception for explicit pre-authorization
- [x] Run eval 36 with_skill and without_skill
- [x] Grade; confirm with_skill 100%, without_skill has at least 1 failing assertion (2 failing: attribution byline and structured issue body)
- [x] Update `evals/pr-comments/benchmark.json`: add eval 36 run entries, update `metadata.evals_run` and `metadata.skill_version` to v1.21 (the version under which Phase 4 runs), recompute `run_summary` stats
- [x] Update `evals/pr-comments/benchmark.md`: add eval 36 section; update "N of M" token denominator sentence
- [x] Update `README.md` Eval Δ column if delta changes

### 4B: Add description trigger phrases
- [x] In `skills/pr-comments/SKILL.md` frontmatter `description` field, add: "fix review feedback", "handle bot review comments", "process Copilot suggestions", "address Claude review"

### 4C: Document concurrent invocation limitation
- [x] In `skills/pr-comments/SKILL.md` Notes section, add bullet:
  "**Concurrent invocations**: Overlapping skill runs on the same PR (e.g., manual invocation while an auto-loop is active) can double-reply or double-resolve threads. Avoid running multiple instances simultaneously."

### Phase 4 verification
- [x] Eval 36 run entries in benchmark.json are consistent with benchmark.md and README
- [x] `npx cspell skills/pr-comments/SKILL.md` — verify new description terms are clean
