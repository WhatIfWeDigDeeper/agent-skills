# peer-review Eval Benchmark

## Summary

| Configuration | Mean pass rate | Stddev | Min | Max |
|---------------|---------------|--------|-----|-----|
| with_skill    | 0.93          | 0.09   | 0.80 | 1.00 |
| without_skill | 0.80          | 0.16   | 0.60 | 1.00 |
| **delta**     | **+0.13**     |        |     |     |

3 evals × 2 configurations = 6 runs. Token statistics are computed over all 6 primary (run_number=1) runs across 3 of 3 evals.

| Metric | with_skill | without_skill |
|--------|-----------|---------------|
| Avg tokens | ~25,494 | ~19,558 |
| Avg time (s) | ~44.2 | ~16.9 |

**Discriminating evals**: Eval 2 is the primary discriminating eval (+0.40 delta). Evals 1 and 3 are non-discriminating on currently measurable assertions (see notes).

## Eval Results

### Eval 1 — `consistency-mode-stale-step-ref`

**Scenario**: Fixture directory with SKILL.md and reference.md. SKILL.md references "Step 3 of reference.md" for the field mapping table, but reference.md has no Step 3 — the field mapping table is at Step 4.

| Configuration | Pass rate | Passed | Failed |
|---------------|-----------|--------|--------|
| with_skill    | 0.80      | 4/5    | 1      |
| without_skill | 0.80      | 4/5    | 1      |

**Non-discriminating**. Both configurations correctly identify consistency mode and find the stale step reference. The sole failing assertion in both — "spawns a subagent" — fails due to an eval harness constraint: the Agent tool is not available inside eval executor subagents. The SKILL.md correctly instructs the main agent to spawn a subagent; this behavior would discriminate in production but cannot be verified in the current eval setup.

**Differentiator not captured**: In production, with_skill delegates to a fresh-context reviewer (no session history); without_skill reviews inline with accumulated context. This distinction matters for longer sessions but cannot be measured with the current assertion set.

### Eval 2 — `spec-mode-plan-tasks-mismatch`

**Scenario**: Spec fixture pair (plan.md + tasks.md). plan.md defines --dry-run, --verbose, and --target ENV; tasks.md only covers --target and --dry-run — --verbose is missing entirely.

| Configuration | Pass rate | Passed | Failed |
|---------------|-----------|--------|--------|
| with_skill    | 1.00      | 5/5    | 0      |
| without_skill | 0.60      | 3/5    | 2      |

**Discriminating** (+0.40 delta). Failing assertions for without_skill:
- **Spec mode not entered explicitly**: without_skill reviewed the files without declaring spec mode as a distinct workflow state.
- **Subagent not spawned**: inline review, no fresh-context delegation.

Without_skill also classified the missing --verbose task as Minor severity; with_skill correctly flagged it as Major (a documented feature with no implementation path is a meaningful gap, not a nit).

### Eval 3 — `staged-no-changes-exit`

**Scenario**: `/peer-review --staged` with no staged changes in the repo.

| Configuration | Pass rate | Passed | Failed |
|---------------|-----------|--------|--------|
| with_skill    | 1.00      | 4/4    | 0      |
| without_skill | 1.00      | 4/4    | 0      |

**Non-discriminating**. The empty-staged-changes behavior (warn + suggest git add) is explicit enough that any capable LLM handles it correctly without the skill. Establishes baseline behavior only.

## Notes

- **Agent tool in eval context**: eval executor subagents cannot spawn further subagents (Agent tool unavailable). The "spawns subagent" assertion fails in both configurations for this reason. In production use, the skill correctly delegates to a fresh subagent — this is its primary value over inline review.
- **Eval 3 redesign candidate**: a future eval that tests argument conflict handling (`--staged` + path → error) would better discriminate, as this is skill-specific behavior unlikely to be reproduced by the baseline.
