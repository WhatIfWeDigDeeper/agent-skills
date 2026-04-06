# Peer-Review v1.4 — Phase IV: Staged/Unstaged Disambiguation, Prompt Quality, Evals

## Context

The peer-review skill (v1.3, 396 lines) has a +30% eval delta and solid coverage, but has two gaps:

1. **When both staged and unstaged changes exist, the user gets no choice** — the skill silently reviews only staged. Users who forget they have unstaged work get an incomplete review without realizing it.
2. **Generic reviewer prompts produce noisy findings** — style preferences, whitespace, obvious-from-context patterns clutter the output. Adding negative guidance ("DO NOT report...") and severity calibration examples will reduce noise.
3. **Eval 2 is nulled** after the v1.3 spec-mode removal and needs re-running with updated assertions.

## Changes

### 1. Auto-detect staged vs. unstaged and prompt when both exist (~10 lines)

**File**: `skills/peer-review/SKILL.md`

No new arguments. Instead, in **Step 2 (Collect Content)**, when the target is staged/default, detect presence first (fast, no content captured):

```bash
git diff --staged --quiet; STAGED_PRESENT=$?
git diff --quiet; UNSTAGED_PRESENT=$?
```
(`0` = nothing present, `1` = changes present)

**Logic:**
- Staged only → collect staged content: `git diff --staged`
- Unstaged only → collect unstaged content: `git diff` — note "No staged changes — reviewing unstaged changes."
- Both present → prompt: "You have both staged and unstaged changes. Review which? [staged/unstaged/all]" and stop generating. On reply, collect the appropriate content:
  - `staged` → `git diff --staged`
  - `unstaged` → `git diff`
  - `all` → `git diff HEAD`
- Neither present → warn "No staged or unstaged changes found. Working tree is clean." and exit

This auto-detect flow only applies when no explicit target is provided. `--branch`, `--pr`, and path targets are unaffected.

The explicit `--staged` flag bypasses detection and always reviews staged only (useful for scripting or when the user knows what they want).

### 2. Improve reviewer prompt quality (~15 lines)

**File**: `skills/peer-review/SKILL.md`

Add noise-reduction guidance to both prompt templates in Step 3.

**Diff mode prompt** — add after the severity guide, before `[DIFF CONTENT]`:
```
Do NOT report:
- Import ordering or grouping preferences
- Whitespace-only issues or formatting style (unless it changes behavior, e.g. Python indentation)
- Missing comments on self-explanatory code
- Suggestions to add type annotations when the file doesn't use them
- Renaming suggestions based on personal preference when the current name is clear

Flag missing test coverage only for non-trivial behavioral changes — not for one-line renames, comment edits, or config tweaks.
```

**Consistency mode prompt** — add after the severity guide, before `[FILE CONTENTS]`:
```
Do NOT report:
- Minor wording preferences that don't change meaning
- Formatting differences between files (indentation, bullet style) unless they signal a copy-paste error
- Issues with content outside the provided files
```

### 3. New evals + eval 2 re-run

**Files**: `evals/peer-review/evals.json`, `evals/peer-review/benchmark.json`, `evals/peer-review/benchmark.md`

- **Re-run eval 2** (`consistency-mode-plan-tasks-mismatch`) — assertions already updated for v1.3; needs a fresh with_skill and without_skill run
- **Add eval 21** (`both-staged-and-unstaged-prompt`) — default target with simulated staged and unstaged changes; verify the skill prompts the user to choose and stops generating
- **Add eval 22** (`unstaged-only-auto-review`) — default target with no staged changes but unstaged changes present; verify the skill reviews unstaged automatically with a note
- **Add eval 23** (`staged-explicit-bypasses-detection`) — `--staged` with both staged and unstaged changes present; verify the skill reviews staged only without prompting

### 4. Tests + version bump

**Files**: `tests/peer-review/conftest.py`, `tests/peer-review/test_peer_review_argument_parsing.py`

- Update `parse_arguments()` / `detect_mode()` in `conftest.py` to handle the staged/unstaged detection logic
- Add test cases for:
  - Both staged and unstaged → prompt path
  - Unstaged only → auto-review unstaged path
  - `--staged` explicit → always staged, no detection
- Bump `metadata.version` from `"1.3"` to `"1.4"` in SKILL.md frontmatter (once per PR)

## Estimated impact

- ~25 lines added to SKILL.md (396 → ~421, well within 500-line budget)
- 3 new evals + 1 re-run
- No new arguments to learn — the skill just does the right thing
- Prompt quality: reduces noisy findings, improves core review value

## Verification

1. `uv run --with pytest pytest tests/peer-review/` — all tests pass
2. `npx cspell skills/peer-review/SKILL.md` — no spelling errors
3. Run evals 2, 21, 22, 23 (with_skill and without_skill), grade, update benchmark
4. Verify SKILL.md line count stays under 500: `wc -l skills/peer-review/SKILL.md`
