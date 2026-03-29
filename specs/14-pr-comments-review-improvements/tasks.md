# Tasks: Spec 14 — pr-comments review improvements

## Phase 1: New Evals (no skill text changes)

### Fix eval 1 conflict (must precede eval 28)
- [x] **Complete all three substeps in order before moving to eval 28 — do not skip ahead:**
  1. In `evals/pr-comments/evals.json` eval 1: rename assertion id `waits-for-confirmation` → `applies-changes-without-confirmation-in-auto-mode` AND update the assertion `text` field from `"The agent waits for user confirmation before proceeding with changes"` → `"In auto mode (default invocation), the agent applies changes without presenting a Proceed? [y/N/auto] prompt"`
  2. In `evals/pr-comments/benchmark.json` eval 1 **without_skill** run entry: replace expectation `text` value `"The agent waits for user confirmation before proceeding with changes"` with `"In auto mode (default invocation), the agent applies changes without presenting a Proceed? [y/N/auto] prompt"` — text-only replacement; `passed: false` and `evidence` remain valid as-is
  3. **Re-run eval 1 with_skill** and replace the stored benchmark.json with_skill entry — the existing entry's evidence ("Step 7 ends with 'Proceed?'") describes pre-v1.16 behavior and is semantically wrong under the new assertion; a fresh run against v1.17 is required to produce valid pass/fail values and evidence. **Gate: do not proceed to eval 28 until this re-run is complete, benchmark.json reflects the new assertion, and the new with_skill evidence confirms auto-mode behavior — the evidence must not mention a `Proceed?` prompt.**

### Auto-mode evals
- [x] Add eval 28 (auto-mode-skips-confirmation) to `evals/pr-comments/evals.json`
- [x] Add eval 29 (auto-iteration-cap) to `evals/pr-comments/evals.json`
- [x] Add eval 30 (manual-to-auto-switch) to `evals/pr-comments/evals.json`

### Security screening evals
- [x] Add eval 31 (hidden-text-injection) to `evals/pr-comments/evals.json`
- [x] Add eval 32 (url-injection) to `evals/pr-comments/evals.json`

### Security screening eval (homoglyph)
- [x] Add eval 33 (homoglyph-injection) to `evals/pr-comments/evals.json`

### Size guard eval
- [x] Add eval 34 (oversized-comment-pauses-auto-mode) to `evals/pr-comments/evals.json`

### Timeline reply format eval
- [x] Add eval 35 (timeline-reply-format) to `evals/pr-comments/evals.json`

### Run and benchmark new evals
- [x] Run evals 28–35 with_skill and without_skill (spawn subagents with `mode: "auto"` to suppress per-tool approval prompts; pass full assertion text strings from `evals.json` explicitly in each subagent prompt so grading.json records the full sentence, not the assertion id)
- [x] Grade results — grading subagent must include a `summary` block in each `grading.json` (`{"summary": {"passed": N, "failed": N, "total": N, "pass_rate": 0.N}, "expectations": [...]}`) or `aggregate_benchmark.py` will report 0% for all runs — and update `evals/pr-comments/benchmark.json`:
  - Add run entries for evals 28–35 (with_skill and without_skill)
  - Append new eval IDs to `metadata.evals_run`
  - Set `metadata.skill_version` to `"1.17"` — all recorded runs are v1.17; do not set to `"1.18"` since no v1.18 runs are being recorded
  - Recompute `run_summary` stats (mean, stddev, min, max) and `delta` from the full runs array; `delta.pass_rate` must use 2-decimal precision (e.g. `"+0.68"`, not `"+0.683"`)
- [x] Confirm all 8 of evals 28–35 pass with_skill; confirm each has at least one failing assertion without_skill
- [x] Update `README.md` Eval Δ column to reflect the new pass-rate delta after all 35 evals (per CLAUDE.md: update immediately after benchmark.json)
- [x] Update `evals/pr-comments/benchmark.md`:
  - Extend the Per-Eval Results summary table (currently ends at eval 23) through eval 35 — ensure exactly one row exists for each of evals 24–35 (add if missing; do not duplicate if already present)
  - In the Per-Eval Results summary table, update the eval 1 row Key differentiators column: remove "confirmation" (search the row for "plan + confirmation" — the cell currently reads "GraphQL thread state, plan + confirmation, Co-authored-by, resolveReviewThread")
  - Add per-eval prose sections for evals 24–27 (currently missing) and 28–35 — ensure exactly one prose section exists per eval (add if missing; do not duplicate if already present); for evals 24–27, locate each run entry by matching `eval_id` in `benchmark.json` and derive prose from: (a) the `expectations` array (what is tested) and (b) the `evidence` strings for both with_skill and without_skill configurations; follow the narrative style of the surrounding eval sections
  - Update all aggregate count references: header, summary sentences, discriminator narrative, and token-stats denominator (currently hardcoded to 27 evals throughout)
  - In the Summary section: update the sentence containing "the interactive plan/confirmation gate" to clarify that in auto mode the plan is shown but no confirmation gate is present
  - In the Eval 1 prose section: update "plan presentation and confirmation gate" → "plan presentation" (eval 1 uses the default auto invocation; no confirmation gate)
  - In the Notes section: update the bullet containing "the plan/confirmation gate" with the same auto-mode clarification
  - In the Notes section: update the bullet containing "Evals 1–6 and 16 have measured timing…time/token fields are `0` or `null`" to reflect that all unknowns are now normalized to `null`
  - Add partial provenance note: "All run entries recorded against v1.17." (the v1.18 validation sentence will be appended after Phase 3 verification)
- [x] Schema hygiene: confirm `eval_name` is present on all benchmark runs (backfill any that lack it); confirm no `tokens: 0` or `time_seconds: 0.0` entries remain for unknown measurements (normalize to `null` if found)
- [x] **Pre-Phase-2 baseline validation**: run full eval suite (all 35 evals) with_skill — confirm no regressions before any skill text changes; validation only, **do not append benchmark run entries** _(full-suite chosen over targeted because Phase 2/3 touch SKILL.md and restructure bot-polling.md entirely, making targeted evals insufficient confidence)_

## Phase 2: Simplify Prescriptive Detail

### SKILL.md changes
- [x] 2A: Remove exact backoff timings — find "2s → 8s → 32s" in `skills/pr-comments/SKILL.md` and rewrite the sentence to read "3-attempt retry with exponential backoff" (drop the specific interval values; preserve the retry-count and mechanism)
- [x] 2D: Condense commit fallback chain — find the "no-gpg-sign" block in `skills/pr-comments/SKILL.md` and replace with: "If the commit fails due to GPG signing, retry with `--no-gpg-sign`. If the heredoc fails, write the message to a temp file via `mktemp`."
  _(Note: 2B and 2C were moved to Phase 3; the labels are intentionally non-contiguous)_
- [x] Pre-bump check (per CLAUDE.md): run `git fetch origin && git diff origin/main -- skills/pr-comments/SKILL.md | rg '^\+  version:'` — only bump if no version increment already exists relative to origin/main
- [x] If pre-bump check finds no existing increment: bump version v1.17 → v1.18

## Phase 3: Restructure bot-polling.md

- [x] Rewrite `skills/pr-comments/references/bot-polling.md` with three-section structure:
  - `## Entry from Step 13` — setup, then reference Shared polling loop
  - `## Entry from Step 6c` — repoll gate (simplified guard), then reference Shared polling loop
  - `## Shared polling loop` — Signals 1–3, poll interval, timeout, exit conditions, auto/manual behavior
- [x] Simplify rapid re-poll guard (current section: `## Rapid re-poll guard (Step 6c loop-backs)`) — replace two-variable state machine with single-sentence principle: "If a Step 6c loop-back already occurred for the same bot set without producing new actionable items, fall through to the 60-second polling loop rather than looping back again"; **documentation-only**: the observable guard behavior (same-bot-set check) is unchanged — do not modify `tests/pr-comments/conftest.py` or `tests/pr-comments/test_bot_poll_routing.py`; after editing, run `rg -n 'last_all_skip|repoll.guard|same.bot' skills/pr-comments/references/bot-polling.md` to confirm no parallel occurrences of the guard logic remain unedited
- [x] Simplify bot display names (current section: `## Bot Display Names`) — replace 4-step algorithm with deterministic 2-step rule: (1) strip `[bot]` suffix; (2) if the result contains hyphens, take the first hyphen-separated token

## Verification

- [x] **Post-Phase-3 regression validation**: run full eval suite (all 35 evals) with_skill — confirm no regressions from Phase 2/3 skill edits; validation only, **do not append benchmark run entries**
- [x] `uv run --with pytest pytest tests/pr-comments/` — all pass
- [x] `npx cspell skills/pr-comments/**/*.md` — no unknown words
- [x] Targeted recheck: evals 9, 12, 13, 14, 22, 23, 29, 30 pass with_skill — eval 9 tests bot display name output (directly affected by the display-name simplification in Phase 3); evals 12/13/14/22/23 are existing polling evals; evals 29/30 are new auto-loop behaviors that exercise the restructured bot-polling.md; validation only, **do not append benchmark run entries**
- [x] Finalize provenance note in `evals/pr-comments/benchmark.md`: append "Full-suite validation against v1.18 was performed and passed but runs are not re-recorded; re-run evals to obtain v1.18 benchmark data."
- [x] Confirm `evals/pr-comments/benchmark.json` `metadata.skill_version` remains `"1.17"` (no v1.18 runs recorded; do not update)
