# Tasks: Spec 13 — pr-comments auto-default

## Implementation

### SKILL.md changes
- [x] Rewrite Arguments section: auto is default, `--manual` restores gate, `--auto [N]` sets cap, update examples table
- [x] Update Step 7: invert condition to "skip gate unless `--manual` was passed"; keep `auto` as mid-session response
- [x] Bump version v1.15 → v1.16

### Reference file changes
- [x] `references/bot-polling.md`: update auto/manual dual-descriptions to reflect new default (auto is default, `--manual` required for manual behavior)
- [x] `references/bot-polling.md`: Step 6c all-skip repoll — update polling prompt to only appear with `--manual`

### Tests
- [x] `conftest.py`: flip `parse_auto_flag()` default to `auto=True`; add `--manual` token detection (sets `auto=False`)
- [x] `test_pr_argument_parsing.py`: update `TestAutoFlagParsing` default expectations; add `TestManualFlagParsing` class; update combined parsing tests
- [x] `test_bot_poll_routing.py`: add assertions for default-auto behavior through the repoll gate (Step 6c) and confirmation-gate routing (Step 7) — verify `--manual` triggers the gate, bare invocation does not

### Docs
- [x] `CLAUDE.md`: update git workflow auto-invocation note (~line 93) — remove explicit `--auto` guidance since it's now the default
- [x] `README.md`: update skill description and Skill Notes to reflect auto-default and `--manual` opt-in

## Verification
- [x] `uv run --with pytest pytest tests/pr-comments/` passes with no failures (189 passed)
- [x] `npx cspell skills/pr-comments/SKILL.md` passes with no unknown words
- [ ] Manual smoke test: `/pr-comments` (no flags) skips Step 7 gate
- [ ] Manual smoke test: `/pr-comments --manual` shows `[y/N/auto]` gate
- [ ] Manual smoke test: `/pr-comments --auto 1` exits after one iteration
- [x] Run targeted evals (20: consistency, 22: early-poll, 23: all-skip repoll) with_skill and without_skill; update `evals/pr-comments/benchmark.json`
- [x] Update `README.md` Eval Δ column to reflect new benchmark pass-rate delta (unchanged at +69%)
