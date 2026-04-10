# Tasks: Spec 20 — pr-comments confirmation prompt dedup & Step 13b/14 gating consolidation

## Phase 1: Extract Step 7 Confirmation Prompt Template

### 1A: Introduce the Confirmation prompt template block

- [x] In `skills/pr-comments/SKILL.md` Step 7, replace the "**Responses (when the confirmation prompt is shown):**" block through the end of Step 7 (SKILL.md:260-269) with the new structure:
  - Define a **Confirmation prompt template** sub-block that contains exactly once:
    - The `Proceed? [y/N/auto]` prompt line
    - Response semantics (`y`, `n`, `auto`) including the `auto` switch-to-auto-mode detail
    - "Output the prompt as your final message and **stop generating**. Do not supply an answer, do not assume `y`, do not continue to Step 8. Resume only after the user replies with `y`, `n`, or `auto`."
  - Define a "**When to show the prompt:**" section with three bullets:
    - **Manual mode (`--manual` was passed)** — always; emit the Confirmation prompt template above
    - **Auto mode (default)** — skip; show the plan table for observability and proceed
    - **Auto mode escalation** — if any condition requires manual confirmation in this iteration (security screening flags from Step 5, oversized comments, diff-validation declines from Step 6, or `consistency` items from Step 6b), drop to manual confirmation and emit the Confirmation prompt template above; `consistency` rows always require explicit confirmation even in auto mode
  - See plan.md for the exact target structure

- [x] Verify load-bearing phrases are all present in the template block — **not** in the branches: `rg -n 'stop generating|do not supply|do not assume|do not continue to Step 8|Resume only after' skills/pr-comments/SKILL.md`
  - Confirm all 5 phrases appear exactly once in Step 7, within the template block

### Phase 1 verification

- [x] `rg -n 'Proceed\? \[y/N/auto\]' skills/pr-comments/SKILL.md` → exactly 2 matches (Arguments section + plan table example; prompt string also now named explicitly in the template block)
- [x] `rg -n 'stop generating' skills/pr-comments/SKILL.md` → no orphaned matches outside the template block (may also appear in `references/bot-polling.md` — those are unrelated and expected)
- [x] `wc -l skills/pr-comments/SKILL.md` → line count dropped by at least 3 vs pre-Phase-1 (457)
- [x] `uv run --with pytest pytest tests/pr-comments/` → all pass

---

## Phase 2: Consolidate Step 13b/14 Gating

### 2A: Replace Step 13b WARNING blockquote

- [x] In `skills/pr-comments/SKILL.md` Step 13b, locate the WARNING blockquote starting at the line containing "WARNING — This step does NOT normally end at Step 14" (around L418)
- [x] Replace the entire WARNING blockquote (the block-quote containing "Step 14 is reachable only through the polling-loop exit conditions...") with a concise 1-2 sentence forward pointer:
  > After the POST below, follow the shared polling flow in `references/bot-polling.md`. See the Step 14 Entry gate for valid exits from Step 13b.

### 2B: Delete numbered list item 4 from Step 13b

- [x] Locate the numbered list in Step 13b starting with "After the POST, execute these in order..." (around L435)
- [x] Delete **item 4** of that list:
  > 4. Step 14 only when `references/bot-polling.md` routes you there: either after the polling flow exits through its defined exit conditions, or immediately after the user declines the manual-mode poll offer
- [x] Retain items 1-3 exactly as-is (they are the concrete resumption checklist):
  1. Confirm the pre-POST snapshot was recorded (timestamp + unresolved thread IDs)
  2. Confirm the POST re-request was sent for each bot reviewer
  3. Resume the shared bot-polling flow in `references/bot-polling.md` after its setup section (do not restart setup, but follow manual-mode poll-offer / stop-and-wait behavior before signal-checking)
- [x] The numbered list introductory phrase ("After the POST, execute these in order — do NOT proceed to Step 14 directly unless...") must also be updated — replace with "After the POST:" to remove the redundant gating language (the Step 14 Entry gate at L444 now owns this constraint)
- [x] Leave the Step 14 Entry gate blockquote (around L444) **unchanged** — it is now the sole authoritative statement

### Phase 2 verification

- [x] `rg -n 'not here yet' skills/pr-comments/SKILL.md` → exactly 1 match (Step 14 Entry gate, unchanged)
- [x] `rg -n 'does NOT normally end at Step 14' skills/pr-comments/SKILL.md` → 0 matches (WARNING removed)
- [x] `rg -n 'do NOT proceed to Step 14' skills/pr-comments/SKILL.md` → 0 matches (list preamble updated)
- [x] `wc -l skills/pr-comments/SKILL.md` → line count ≤ 446 (target -11 to -13 from 457)
- [x] `uv run --with pytest pytest tests/pr-comments/` → all pass

---

## Phase 3: Version Bump and Final Verification

- [x] Pre-bump check: `git fetch origin && git diff origin/main -- skills/pr-comments/SKILL.md | rg '^\+  version:'` — only bump if no increment already exists relative to origin/main
- [x] If check is clean: bump version v1.25 → v1.26 in `skills/pr-comments/SKILL.md` frontmatter `metadata.version` field
- [x] `npx cspell skills/pr-comments/SKILL.md` → no unknown words; add any new terms to `cspell.config.yaml` if introduced
- [x] **Eval regression spot-check** (simulated transcripts; documentation-only changes; do not append benchmark run entries):
  - Run eval 1 (basic flow, Step 7/8/13b) with_skill → 100% pass
  - Run eval 12 (bot poll loopback — Step 13b → bot-polling.md handoff) with_skill → 100% pass
  - Run eval 28 (auto-mode-skips-confirmation — Step 7) with_skill → 100% pass
  - Run eval 34 (oversized-comment-pauses-auto-mode — Step 7 escalation branch) with_skill → 100% pass
  - If any assertion text references the exact pre-edit wording being removed, update the assertion text in `evals/pr-comments/evals.json` and the corresponding expectation `text` in `benchmark.json` as part of this PR (per CLAUDE.md "renaming action labels or vocabulary" rule — check both assertion `text` and eval `expected_output` fields: `rg '"text":.*Proceed\?|not here yet|stop generating' evals/pr-comments/`)
- [x] `rg -n 'Proceed\? \[y/N/auto\]' evals/pr-comments/evals.json evals/pr-comments/benchmark.json` — if any expectation text contains the old multi-sentence "stop generating" block verbatim, update to match new wording
- [x] `git diff --stat` — confirm only `skills/pr-comments/SKILL.md` and `specs/20-pr-comments-confirmation-and-gating-cleanup/` were modified (no eval/test/reference-file changes)
