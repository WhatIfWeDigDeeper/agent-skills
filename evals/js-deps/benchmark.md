# js-deps Benchmark Results

**Model**: claude-sonnet-4-6
**Date**: 2026-03-15
**Evals**: 5 (1 run each, with-skill vs. without-skill)

## Summary

| Metric | with-skill | without-skill | Delta |
|--------|-----------|--------------|-------|
| Pass rate | **93.3%** ± 14.9% | 55.3% ± 24.4% | **+38%** |
| Time | 77.1s ± 25.2s | 53.8s ± 26.4s | +23.3s |
| Tokens | 21,430 ± 2,473 | 15,722 ± 3,121 | +5,708 |

The skill adds time and tokens (expected — it loads reference files and follows a more thorough workflow) and improves correctness by +38 percentage points on average.

## Per-Eval Results

| # | Eval | with-skill | without-skill | Key differentiators |
|---|------|-----------|--------------|---------------------|
| 1 | Security audit | **5/5 (100%)** | 1/5 (20%) | Worktree isolation, install-skip, severity filter, cleanup |
| 2 | Help flag (`--help`) | 2/3 (67%) | 2/3 (67%) | Tied — AskUserQuestion unavailable in both eval runs |
| 3 | Update all to latest | **5/5 (100%)** | 2/5 (40%) | Worktree, install-before-outdated, major-bump commit format |
| 4 | Specific packages | **4/4 (100%)** | 3/4 (75%) | AskUserQuestion for scope vs. autonomous default |
| 5 | Critical-only audit | **4/4 (100%)** | 3/4 (75%) | Worktree; severity inference correct in both |

## What Each Eval Tests

### Eval 1 — Security audit
**Prompt**: `run a security audit on my node project`

Tests the core security workflow: creating a worktree before touching anything, skipping `npm install` (audit reads from lock files), applying the default Critical+High filter, and always cleaning up afterward. The without-skill run skipped the worktree entirely and applied no severity filter.

### Eval 2 — Help flag
**Prompt**: `/js-deps --help`

Tests the interactive help flow: displaying the summary and presenting a workflow selection question via `AskUserQuestion`. Both runs scored 2/3 — `AskUserQuestion` is unavailable to subagents in the eval environment, so assertion 2 always fails. The with-skill run reached the correct step and fell back to plain text.

### Eval 3 — Update all
**Prompt**: `update all my js packages to the latest versions`

Tests the update workflow: worktree, running `npm install` before `npm outdated` (without it, exact-pinned packages are invisible), inferring Patch+Minor+Major from "latest", validating after updates, and noting major version bumps in the commit message. The without-skill run lacked the worktree, ran the outdated check before install, and used a generic commit message.

### Eval 4 — Specific packages
**Prompt**: `/js-deps react react-dom @types/react`

Tests scoped updates: only targeting the named packages, filtering install directories to those containing at least one named package, and asking the user about version scope (since no preference was expressed). The without-skill run autonomously defaulted to staying within the current major instead of asking.

### Eval 5 — Critical-only audit
**Prompt**: `fix only critical security vulnerabilities in my project`

Tests inline severity inference (no interactive question needed) and the audit-skips-install rule. Both runs correctly inferred critical-only scope. The without-skill run dropped 1 point for skipping the worktree.

## Historical Comparison

| Run | Date | with-skill | without-skill | Delta |
|-----|------|-----------|--------------|-------|
| v0.6 (pre-worktree-fallback) | 2026-03-15 | 81.4% | 24.6% | +57% |
| v0.7 (current) | 2026-03-15 | 93.3% | 55.3% | +38% |

The apparent delta reduction (+57% → +38%) is explained by the without-skill baseline improving significantly on evals 4 and 5 in this run. The with-skill score improved meaningfully on eval 1 (40% → 100%) due to the worktree fallback to `$TMPDIR` introduced in v0.7.

## Known Eval Limitations

See [README.md](README.md) for full details. Key points:
- All evals are narrated/simulated — no real JS project fixture exists in this repo. Assertions verify planned behavior, not actual execution.
- `AskUserQuestion` is unavailable to subagents, so eval 2's assertion 2 always fails in this environment.
- Eval 1's previous low score (40%) was an environment artifact; the worktree sandbox restriction blocked the old single-path approach. The `$TMPDIR` fallback in v0.7 resolves this.
