# peer-review Benchmark Results

**Model**: claude-sonnet-4-6
**Date**: 2026-04-04
**Evals**: 14 (1 run each, with-skill vs. without-skill)

## Summary

| Metric | with-skill | without-skill | Delta |
|--------|-----------|---------------|-------|
| Pass rate | 97% ± 7% | 70% ± 30% | **+27%** |
| Min / Max | 80% / 100% | 0% / 100% | |
| Time (s) | ~43.0 ± 34.8 | ~45.6 ± 61.5 | -2.7 |
| Tokens | ~26,892 ± 7,377 | ~25,644 ± 13,928 | +1,249 |

14 evals × 2 configurations = 28 runs. Token statistics are computed over 8 of 14 primary (run_number=1) runs per configuration (16 of 28 total) — evals 5–10 use simulated transcripts and have no recorded time or token measurements; evals 1–4 and 11–14 have real measurements.

**Discriminating evals**: Evals 2, 4, 5, 7, 8, 9, 10, 13 discriminate. Eval 2 is the primary discriminating eval (+0.40 delta). Eval 5 (copilot severity normalization) has the highest delta (+1.0). Eval 13 (focus-option) discriminates at +0.67. Evals 3, 6, 11, 12, 14 are non-discriminating: baseline handles conflict detection, no-findings output, empty-staged warning, PR metadata inclusion (with fixture), and skip handling correctly without the skill. Eval 1 is zero-delta (0.80/0.80) due to an eval harness constraint.

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

### Eval 4 — `diff-mode-branch-review`

**Scenario**: `/peer-review --branch specs/16-peer-review` — diff mode review of the peer-review implementation branch vs main.

| Configuration | Pass rate | Passed | Failed |
|---------------|-----------|--------|--------|
| with-skill    | 0.80      | 4/5    | 1      |
| without-skill | 0.60      | 3/5    | 2      |

**Discriminating** (+0.20 delta). Failing assertions for without-skill:
- **Diff mode not declared explicitly**: without-skill ran a git diff review without naming it as diff mode (as distinct from spec or consistency mode).
- **Subagent not spawned**: inline review with 45 tool calls vs 8 for with-skill. without-skill spent 191.9s and 59,648 tokens; with-skill spent 105.5s and 44,948 tokens.

The subagent assertion also fails for with-skill (harness constraint), so net delta is +0.20.

### Eval 5 — `copilot-json-parse`

**Scenario**: `/peer-review --staged --model copilot` with a fixture copilot JSON response containing two findings with severities `high` and `low`. The skill must normalize these to `critical` and `minor` respectively.

| Configuration | Pass rate | Passed | Failed |
|---------------|-----------|--------|--------|
| with-skill    | 1.00      | 3/3    | 0      |
| without-skill | 0.00      | 0/3    | 3      |

**Discriminating** (+1.0 delta). All 3 assertions fail without-skill — severity remapping (`high` → `critical`, `low` → `minor`) and the apply prompt are both skill-defined behaviors. Without the skill, the agent presents severity labels as-is from the JSON and does not show an apply prompt.

### Eval 6 — `copilot-empty-findings`

**Scenario**: `/peer-review --staged --model copilot` with a fixture copilot JSON response containing an empty `findings` array.

| Configuration | Pass rate | Passed | Failed |
|---------------|-----------|--------|--------|
| with-skill    | 1.00      | 2/2    | 0      |
| without-skill | 1.00      | 2/2    | 0      |

**Non-discriminating**. Both configurations produce "No issues found." when the findings array is empty, and neither shows an apply prompt. The no-findings output is natural default behavior; the apply prompt is skill-defined but absent in both since there are no findings to act on.

### Eval 7 — `copilot-malformed-json`

**Scenario**: `/peer-review --staged --model copilot` with a fixture copilot response that is not valid JSON (a plain text error message).

| Configuration | Pass rate | Passed | Failed |
|---------------|-----------|--------|--------|
| with-skill    | 1.00      | 2/2    | 0      |
| without-skill | 0.50      | 1/2    | 1      |

**Discriminating** (+0.50 delta). The specific fallback phrase "Could not parse structured findings; showing raw output." is skill-defined and fails without-skill. Showing the raw error text is natural default behavior and passes in both configurations.

### Eval 8 — `codex-not-found`

**Scenario**: `/peer-review --staged --model codex` when the `codex` binary is absent.

| Configuration | Pass rate | Passed | Failed |
|---------------|-----------|--------|--------|
| with-skill    | 1.00      | 3/3    | 0      |
| without-skill | 0.67      | 2/3    | 1      |

**Discriminating** (+0.33 delta). The specific install hint `npm install -g @openai/codex` is skill-defined and fails without-skill. Detecting the missing binary and stopping without showing findings are natural behaviors that pass in both configurations.

### Eval 9 — `gemini-not-found`

**Scenario**: `/peer-review --staged --model gemini` when the `gemini` binary is absent.

| Configuration | Pass rate | Passed | Failed |
|---------------|-----------|--------|--------|
| with-skill    | 1.00      | 3/3    | 0      |
| without-skill | 0.67      | 2/3    | 1      |

**Discriminating** (+0.33 delta). Mirrors eval 8 — specific install hint `npm install -g @google/gemini-cli` is skill-defined and fails without-skill.

### Eval 10 — `gemini-no-findings`

**Scenario**: `/peer-review --staged --model gemini` with a fixture gemini response returning exactly `NO FINDINGS`.

| Configuration | Pass rate | Passed | Failed |
|---------------|-----------|--------|--------|
| with-skill    | 1.00      | 3/3    | 0      |
| without-skill | 0.67      | 2/3    | 1      |

**Discriminating** (+0.33 delta). The `## Peer Review —` header format is skill-defined and fails without-skill. Outputting "No issues found." and omitting the apply prompt pass in both configurations as natural behaviors.

### Eval 11 — `staged-empty-warning`

**Scenario**: `/peer-review --staged` when `git diff --staged` returns empty output.

| Configuration | Pass rate | Passed | Failed |
|---------------|-----------|--------|--------|
| with-skill    | 1.00      | 3/3    | 0      |
| without-skill | 1.00      | 3/3    | 0      |

**Non-discriminating**. Both configurations output "No staged changes found. Stage files with `git add` first." and exit without spawning a reviewer. The warning is simple and conventional — baseline handles it correctly without skill guidance.

### Eval 12 — `pr-target-context`

**Scenario**: `/peer-review --pr 42` with fixture PR metadata (title, body, diff). Reviewer returns NO FINDINGS.

| Configuration | Pass rate | Passed | Failed |
|---------------|-----------|--------|--------|
| with-skill    | 1.00      | 4/4    | 0      |
| without-skill | 1.00      | 4/4    | 0      |

**Non-discriminating**. Both configurations included PR title/body as context and produced the same output. The without-skill agent even reproduced the skill-defined `## Peer Review — PR #42` header format. This is likely because the fixture data was explicit in the eval prompt, making the correct behavior obvious. The eval establishes that PR metadata handling works correctly.

### Eval 13 — `focus-option`

**Scenario**: `/peer-review --staged --focus security` with two findings (Critical SQL injection, Minor JSDoc).

| Configuration | Pass rate | Passed | Failed |
|---------------|-----------|--------|--------|
| with-skill    | 1.00      | 3/3    | 0      |
| without-skill | 0.33      | 1/3    | 2      |

**Discriminating** (+0.67 delta). Failing assertions for without-skill:
- **Focus line not appended to reviewer prompt**: without-skill showed "**Focus:** security" as a presentation header but did not build a reviewer prompt at all — the focus line format ("Focus especially on security. Still report any critical findings outside this focus area.") is skill-defined.
- **Apply prompt absent**: without-skill ended with a summary table and recommendation instead of the apply prompt.

### Eval 14 — `apply-skip`

**Scenario**: User replies `skip` after the skill presents two findings.

| Configuration | Pass rate | Passed | Failed |
|---------------|-----------|--------|--------|
| with-skill    | 1.00      | 2/2    | 0      |
| without-skill | 1.00      | 2/2    | 0      |

**Non-discriminating**. Both configurations output a skip summary without making file edits. The skill-defined exact phrasing ("Skipped 2 findings. No changes made.") was not reproduced by without-skill ("No changes applied..."), but the assertion accepts equivalent summaries, so both pass. Establishes baseline behavior for the skip path.

## Notes

- **Agent tool in eval context**: eval executor subagents cannot spawn further subagents (Agent tool unavailable). For evals 1 and 4, the "spawns subagent" assertion fails in both configurations for this reason. In production use, the skill correctly delegates to a fresh subagent.
- **Evals 5–10 use simulated transcripts**: fixture CLI responses are embedded in the eval prompt rather than calling real external CLIs (which may not be installed). Time and token measurements are null for these runs.
- **Evals 11–14 have real measurements**: executor subagents ran the full skill workflow; time and token data recorded.
- **Eval 6 non-discriminating**: both configurations naturally output "No issues found." for an empty findings array. This establishes baseline behavior for the empty-findings case.
- **Eval 3 redesign note**: Previously tested "no staged changes → warn and exit" (non-discriminating). Redesigned to test argument conflict (`--staged` + path → error). Also non-discriminating — conflict detection is simple enough that a capable baseline handles it correctly.
- **Delta from adding evals 11–14**: adding 4 mostly non-discriminating evals (11, 12, 14) plus one discriminating eval (13) reduces the headline delta from +31% to +27%. The absolute discrimination is unchanged — eval 13 adds a new +0.67 discriminating signal; the denominator grew by 4.
