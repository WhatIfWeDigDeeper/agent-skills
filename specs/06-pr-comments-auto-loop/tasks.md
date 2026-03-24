# Tasks: Spec 06 — pr-comments Auto-Loop Mode

## Implementation

- [x] Update `skills/pr-comments/SKILL.md` — add `--auto [N]` argument, Step 7 `auto` response, Step 13 auto/manual poll split, PR metadata update, human reviewer re-request, auto-loop summary in Step 14, Notes update, version bump to 1.5
- [x] Update `tests/pr-comments/conftest.py` — add `parse_auto_flag()` and `should_exit_auto_loop()` helpers
- [x] Update `tests/pr-comments/test_pr_argument_parsing.py` — add `TestAutoFlagParsing` class
- [x] Update `tests/pr-comments/test_bot_poll_routing.py` — add `TestAutoLoopExitConditions` class
- [x] Update `README.md` — update pr-comments description and trigger examples

## Verification

- [ ] Run `uv run --with pytest pytest tests/pr-comments/` — all existing + new tests pass
- [ ] Manual test on a PR with Copilot reviewer to verify full auto-loop cycle end-to-end
- [ ] Verify PR title/body updates with `gh pr view --json title,body` after auto-loop
- [ ] Add new eval scenarios to `evals/pr-comments/evals.json`:
  - Auto-loop happy path (2–3 iterations, clean exit on no new threads)
  - `--auto` with no bot reviewers (fallback to normal mode)
  - Security flag during auto-loop (pause, manual confirm, resume offer)
  - Max iteration exit
  - Interactive `auto` entry at Step 7 prompt
- [ ] Run full eval suite (existing 16 + new scenarios), update `evals/pr-comments/benchmark.json`
- [ ] Update `Eval Δ` column in `README.md` with new pass-rate delta
