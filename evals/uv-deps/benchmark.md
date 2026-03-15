# uv-deps Benchmark Results

**Model**: claude-sonnet-4-6
**Date**: 2026-03-11
**Evals**: 5 (1 run each, with-skill vs. without-skill)

## Summary

| Metric | with-skill | without-skill | Delta |
|--------|-----------|--------------|-------|
| Pass rate | **100.0%** ± 0.0% | 17.2% ± 14.8% | **+83%** |
| Time | 114.4s ± 47.7s | 39.6s ± 13.1s | +74.8s |
| Tokens | 43,100 ± 18,227 | 14,900 ± 6,184 | +28,200 |

The skill adds significant overhead (~75s, ~28k tokens) and improves correctness by +83 percentage points. The overhead is expected: worktree creation, reference file reads, GHSA severity lookups, sequential update loops, and commit/PR creation all contribute. High time variance in the with-skill runs reflects the wide range of workflows (22s for help display vs. 155s for full update).

## Per-Eval Results

| # | Eval | with-skill | without-skill | Key differentiators |
|---|------|-----------|--------------|---------------------|
| 1 | Security audit | **5/5 (100%)** | 0/5 (0%) | Worktree, uv export pipeline, Critical+High filter, cleanup |
| 2 | Help invocation | **3/3 (100%)** | 1/3 (33%) | Help summary display, AskUserQuestion for workflow selection |
| 3 | Update to latest | **5/5 (100%)** | 1/5 (20%) | Worktree, uv pip list --outdated, sequential updates |
| 4 | Specific packages | **3/3 (100%)** | 1/3 (33%) | Worktree, AskUserQuestion for version scope |
| 5 | Critical-only audit | **4/4 (100%)** | 0/4 (0%) | Worktree, inline severity parse, Critical-only filter, correct reference file |

## What Each Eval Tests

### Eval 1 — Security audit
**Prompt**: `run a security audit on my Python project`

Tests the core audit workflow: creating a worktree before any changes, reading `references/audit-workflow.md`, running the `uv export --frozen | uvx pip-audit` pipeline (not direct pip-audit), applying the default Critical+High severity filter, and cleaning up the worktree at the end. The without-skill run skipped the worktree, used direct pip-audit, and applied no severity filter.

### Eval 2 — Help invocation
**Prompt**: `/uv-deps --help`

Tests the interactive help flow: displaying the skill summary with workflow descriptions from `references/interactive-help.md`, then presenting a workflow selection question via `AskUserQuestion` before starting anything. The without-skill run had no knowledge of uv-deps workflows — it ran `uv --help` rather than displaying skill-specific options. The without-skill "no worktree" assertion passes vacuously (the agent doesn't start any workflow at all).

### Eval 3 — Update to latest
**Prompt**: `update all my Python packages to the latest versions`

Tests the update workflow: worktree creation, reading `references/update-workflow.md`, running `uv pip list --outdated` to identify candidates, inferring Patch+Minor+Major scope from "latest versions" (no question needed), and updating packages sequentially to avoid `uv.lock` contention. The without-skill run lacked the worktree, used pip instead of uv, and batched updates rather than running them sequentially.

### Eval 4 — Specific packages
**Prompt**: `/uv-deps requests tomli`

Tests scoped updates: only targeting the named packages (not all packages), creating a worktree before making changes, and asking the user about version scope via `AskUserQuestion` since no scope preference was expressed. The without-skill run correctly targeted only the named packages (natural from the prompt) but skipped the worktree and version scope question.

### Eval 5 — Critical-only audit
**Prompt**: `fix only critical security vulnerabilities in my Python project`

Tests inline severity inference: the word "critical" in the prompt should set `SELECTED_SEVERITIES=critical` without asking. Also tests that the correct reference file (`audit-workflow.md`, not `update-workflow.md`) is loaded. The without-skill run lacked the GHSA lookup workflow needed for severity filtering — pip-audit has no built-in `--severity` flag.

## Known Eval Limitations

- All evals are narrated/simulated — no real Python project fixture is used for evals 2 and 4. Evals 1, 3, and 5 use the fixture in `evals/uv-deps/fixtures/`.
- Eval 2 and eval 4: the "no worktree" and "targets specific packages" assertions pass vacuously for without-skill. These are non-discriminating assertions for the baseline.
- Eval 3: the "latest versions scope inference" assertion passes for without-skill — natural language inference that Claude does well regardless of skill guidance.
- Severity filtering is the primary technical differentiator: without the GHSA lookup workflow, agents lack a mechanism to filter by severity since pip-audit has no `--severity` flag.
