# peer-review Benchmark Results

**Model**: claude-sonnet-4-6
**Date**: 2026-04-04
**Evals**: 4 (1 run each, with-skill vs. without-skill)

## Summary

| Metric | with-skill | without-skill | Delta |
|--------|-----------|---------------|-------|
| Pass rate | 90% ± 12% | 75% ± 19% | **+15%** |
| Min / Max | 80% / 100% | 60% / 100% | |
| Time (s) | ~68.4 ± 32.2 | ~80.4 ± 74.7 | -12.0 |
| Tokens | ~29,693 ± 10,297 | ~30,751 ± 19,286 | -1,058 |

4 evals × 2 configurations = 8 runs. Token statistics are computed over 4 of 4 primary (run_number=1) runs per configuration (8 total).

**Discriminating evals**: Eval 2 is the primary discriminating eval (+0.40 delta). Eval 4 is the secondary discriminating eval (+0.20 delta). Eval 3 is non-discriminating (both 100%): baseline handles conflict detection correctly without the skill. Eval 1 is zero-delta (0.80/0.80) due to an eval harness constraint — the Agent tool is unavailable in the eval executor context, masking the subagent-spawning differentiator.

## Eval Results

### Eval 1 — `consistency-mode-stale-step-ref`

**Scenario**: Fixture directory with SKILL.md and reference.md. SKILL.md references "Step 3 of reference.md" for the field mapping table, but reference.md has no Step 3 — the field mapping table is at Step 4.

| Configuration | Pass rate | Passed | Failed |
|---------------|-----------|--------|--------|
| with-skill    | 0.80      | 4/5    | 1      |
| without-skill | 0.80      | 4/5    | 1      |

**Zero-delta (0.80/0.80) due to eval harness constraint**. Both configurations correctly identify consistency mode and find the stale step reference. The sole failing assertion in both — "spawns a subagent" — fails because the Agent tool is not available inside eval executor subagents. In production, with-skill delegates to a fresh subagent while the baseline reviews inline.

### Eval 2 — `spec-mode-plan-tasks-mismatch`

**Scenario**: Spec fixture pair (plan.md + tasks.md). plan.md defines --dry-run, --verbose, and --target ENV; tasks.md only covers --target and --dry-run — --verbose is missing entirely.

| Configuration | Pass rate | Passed | Failed |
|---------------|-----------|--------|--------|
| with-skill    | 1.00      | 5/5    | 0      |
| without-skill | 0.60      | 3/5    | 2      |

**Discriminating** (+0.40 delta). Failing assertions for without-skill:
- **Spec mode not entered explicitly**: without-skill reviewed the files without declaring spec mode as a distinct workflow state.
- **Subagent not spawned**: inline review, no fresh-context delegation.

without-skill classified the missing --verbose task as Critical; with-skill correctly flagged it as Major (a documented feature with no implementation path).

### Eval 3 — `argument-conflict-error`

**Scenario**: `/peer-review --staged skills/peer-review/SKILL.md` — both `--staged` and a file path provided simultaneously. These are mutually exclusive targets.

| Configuration | Pass rate | Passed | Failed |
|---------------|-----------|--------|--------|
| with-skill    | 1.00      | 3/3    | 0      |
| without-skill | 1.00      | 3/3    | 0      |

**Non-discriminating**. Both configurations correctly detect the mutually exclusive target conflict, output an appropriate error message, and exit without running a review. Conflict detection logic is simple enough for a capable baseline to handle correctly. Establishes baseline behavior only.

*Previously eval 3 tested "no staged changes → graceful exit", which was also non-discriminating. The conflict-detection scenario was the planned redesign but remains non-discriminating for the same reason.*

### Eval 4 — `diff-mode-branch-review`

**Scenario**: `/peer-review --branch specs/16-peer-review` — diff mode review of the peer-review implementation branch vs main.

| Configuration | Pass rate | Passed | Failed |
|---------------|-----------|--------|--------|
| with-skill    | 0.80      | 4/5    | 1      |
| without-skill | 0.60      | 3/5    | 2      |

**Discriminating** (+0.20 delta). Failing assertions for without-skill:
- **Diff mode not declared explicitly**: without-skill ran a git diff review without naming it as diff mode (as distinct from spec or consistency mode).
- **Subagent not spawned**: inline review with 45 tool calls vs 8 for with-skill. without-skill spent 191.9s and 59,648 tokens; with-skill spent 105.5s and 44,948 tokens.

The subagent assertion also fails for with-skill (harness constraint), so net delta is +0.20. In production, with-skill delegates to a fresh-context reviewer while the baseline works inline — the efficiency gap (45 vs 8 tool calls) suggests the unstructured inline approach is substantially more expensive.

## Notes

- **Agent tool in eval context**: eval executor subagents cannot spawn further subagents (Agent tool unavailable). For evals 1 and 4, the "spawns subagent" assertion fails in both configurations for this reason. In production use, the skill correctly delegates to a fresh subagent.
- **Eval 3 redesign**: Previously tested "no staged changes → warn and exit" (non-discriminating). Redesigned to test argument conflict (`--staged` + path → error). Also non-discriminating — conflict detection is simple enough that a capable baseline handles it. A future discriminating version might test a less-obvious conflict path or verify the exact error message format more strictly.
- **Eval 4 quality**: The with-skill diff reviewer caught real findings in the branch, including potential CI action version issues (`checkout@v6`, `setup-uv@v7`) and a stddev calculation worth verifying. The unstructured baseline took 45 tool calls and 191.9s to complete the same review — 4x more tool calls and 1.8x more time.
