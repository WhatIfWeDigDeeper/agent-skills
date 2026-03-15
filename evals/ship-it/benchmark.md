# ship-it Benchmark Results

**Model**: claude-sonnet-4-6
**Date**: 2026-03-11
**Evals**: 3 (1 run each, with-skill vs. without-skill)

## Summary

| Metric | with-skill | without-skill | Delta |
|--------|-----------|--------------|-------|
| Pass rate | **100.0%** ± 0.0% | 62.5% ± 0.0% | **+38%** |
| Time | 115.7s ± 4.3s | 74.7s ± 14.8s | +41.0s |
| Tokens | 21,335 ± 1,203 | 16,262 ± 1,668 | +5,073 |

The skill adds ~41s and ~5000 tokens overhead and improves correctness by +38 percentage points. The baseline consistently scores 62.5% — it naturally produces good branch names, commit messages, and PR bodies, but reliably skips the three process safety checks the skill mandates.

## Per-Eval Results

| # | Eval | with-skill | without-skill | Key differentiators |
|---|------|-----------|--------------|---------------------|
| 1 | Bug fix (null check) | **8/8 (100%)** | 5/8 (62.5%) | git fetch divergence check, ls-remote collision check, --base flag |
| 2 | Draft PR (WIP feature) | **8/8 (100%)** | 5/8 (62.5%) | Same three process assertions; draft detection passes in both |
| 3 | Refactor with explicit branch | **8/8 (100%)** | 5/8 (62.5%) | Same three process assertions; branch name passed explicitly |

## What Each Eval Tests

### Eval 1 — Bug fix (null check)
**Prompt**: User has uncommitted changes fixing null checks in a users API; wants to ship it.

Tests the full ship-it workflow: branch naming with `fix/` prefix, conventional commit format, PR body with Summary + Test Plan, no sensitive files staged, divergence check via `git fetch`, branch collision check via `git ls-remote --heads origin`, and `--base` flag on `gh pr create`. The without-skill run produced a correct branch, commit, and PR body — but skipped all three process checks.

### Eval 2 — Draft PR (WIP feature)
**Prompt**: Partial onboarding feature with TODO comments; should be opened as a draft PR.

Tests draft detection in addition to the standard workflow. Both configurations correctly detected draft mode from the "prototyping" context and TODO comments. The without-skill run again skipped the divergence check, collision check, and `--base` flag — the same three omissions as eval 1.

### Eval 3 — Refactor with explicit branch name
**Prompt**: `/ship-it refactor/auth-service` — user specifies the exact branch name.

Tests that the skill respects an explicit branch name from `$ARGUMENTS` rather than generating one. Both runs used the provided `refactor/auth-service` name. The without-skill run followed the same pattern: strong output quality but absent process steps.

## Notes

- Output quality assertions (branch prefix, commit format, PR structure) pass in both configurations — Claude naturally produces these without skill guidance.
- The three consistently failing assertions in the without-skill runs are all omissions (things not done), not errors. The baseline doesn't do the wrong thing; it skips safety steps.
- Zero variance in without-skill pass rates (62.5% across all 3 evals) suggests a stable capability boundary: Claude will write good PRs on its own, but the three process checks require explicit instruction.
