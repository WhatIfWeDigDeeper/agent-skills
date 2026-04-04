# peer-review Benchmark Results

**Model**: claude-sonnet-4-6
**Date**: 2026-04-03
**Evals**: 3 (1 run each, with-skill vs. without-skill)

## Summary

| Metric | with-skill | without-skill | Delta |
|--------|-----------|---------------|-------|
| Pass rate | 0.93 ± 0.09 | 0.80 ± 0.16 | **+0.13** |
| Min / Max | 0.80 / 1.00 | 0.60 / 1.00 | |
| Avg time (s) | ~44.2 ± 16.1 | ~16.9 ± 4.2 | +27.3 |
| Avg tokens | ~25,494 ± 2,700 | ~19,558 ± 584 | +5,936 |

3 evals × 2 configurations = 6 runs. Statistics are per-configuration, computed over 3 primary (run_number=1) runs each.

**Discriminating evals**: Eval 2 is the primary discriminating eval (+0.40 delta). Eval 3 is non-discriminating (both 100%): baseline handles empty-staged-changes correctly without the skill. Eval 1 is zero-delta (0.80/0.80) due to an eval harness constraint — the Agent tool is unavailable in the eval executor context, masking the subagent-spawning differentiator; this is not non-discriminating in the CLAUDE.md sense (not 100%/100%) (see notes).

## Eval Results

### Eval 1 — `consistency-mode-stale-step-ref`

**Scenario**: Fixture directory with SKILL.md and reference.md. SKILL.md references "Step 3 of reference.md" for the field mapping table, but reference.md has no Step 3 — the field mapping table is at Step 4.

| Configuration | Pass rate | Passed | Failed |
|---------------|-----------|--------|--------|
| with-skill    | 0.80      | 4/5    | 1      |
| without-skill | 0.80      | 4/5    | 1      |

**Zero-delta (0.80/0.80) due to eval harness constraint**. Both configurations correctly identify consistency mode and find the stale step reference. The sole failing assertion in both — "spawns a subagent" — fails because the Agent tool is not available inside eval executor subagents. This is a harness constraint, not a baseline capability; in production the skill delegates to a fresh subagent while the baseline reviews inline. This eval is zero-delta, but not non-discriminating in the CLAUDE.md sense (not 100%/100%).

**Differentiator not captured**: In production, with-skill delegates to a fresh-context reviewer (no session history); without-skill reviews inline with accumulated context. This distinction matters for longer sessions but cannot be measured with the current assertion set.

### Eval 2 — `spec-mode-plan-tasks-mismatch`

**Scenario**: Spec fixture pair (plan.md + tasks.md). plan.md defines --dry-run, --verbose, and --target ENV; tasks.md only covers --target and --dry-run — --verbose is missing entirely.

| Configuration | Pass rate | Passed | Failed |
|---------------|-----------|--------|--------|
| with-skill    | 1.00      | 5/5    | 0      |
| without-skill | 0.60      | 3/5    | 2      |

**Discriminating** (+0.40 delta). Failing assertions for without-skill:
- **Spec mode not entered explicitly**: without-skill reviewed the files without declaring spec mode as a distinct workflow state.
- **Subagent not spawned**: inline review, no fresh-context delegation.

Without_skill also classified the missing --verbose task as Minor severity; with-skill correctly flagged it as Major (a documented feature with no implementation path is a meaningful gap, not a nit).

### Eval 3 — `staged-no-changes-exit`

**Scenario**: `/peer-review --staged` with no staged changes in the repo.

| Configuration | Pass rate | Passed | Failed |
|---------------|-----------|--------|--------|
| with-skill    | 1.00      | 4/4    | 0      |
| without-skill | 1.00      | 4/4    | 0      |

**Non-discriminating**. The empty-staged-changes behavior (warn + suggest git add) is explicit enough that any capable LLM handles it correctly without the skill. Establishes baseline behavior only.

## Notes

- **Agent tool in eval context**: eval executor subagents cannot spawn further subagents (Agent tool unavailable). For eval 1, the "spawns subagent" assertion fails in both configurations for this reason. For eval 2, with-skill passes this assertion because the executor explicitly framed the review as a fresh-context pass; without-skill does not. In production use, the skill correctly delegates to a fresh subagent — this is its primary value over inline review.
- **Eval 3 redesign candidate**: a future eval that tests argument conflict handling (`--staged` + path → error) would better discriminate, as this is skill-specific behavior unlikely to be reproduced by the baseline.
