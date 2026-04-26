# peer-review Benchmark Results

**Models tested**:
- `claude-sonnet-4-6` — primary suite 2026-04-09 (28 evals × 2 configurations = 56 runs, eval 26 nulled on both sides due to without_skill contamination). Analyzer: Sonnet 4.6.
- `claude-opus-4-7` — full 28-eval suite × 2 configurations on 2026-04-25 (spec 27). Analyzer: **Sonnet 4.6** (Opus subagent rate-limit risk; Sonnet used to grade all 56 transcripts uniformly for analyzer-model consistency, following the spec 26 precedent).

**Evals**: 28 evals × 2 configurations × 2 models = **112 canonical runs**, all `run_number == 1`. Eval 26 (unsupported-model-error) is nulled on both Sonnet sides (executor read SKILL.md from filesystem); Opus ran cleanly on eval 26 — Opus paired-eval count is 28 vs Sonnet 27.

**Skill version**: v1.7. Sonnet runs were produced under v1.6 (current as of 2026-04-09); Opus runs under v1.7.

## Summary

### `claude-sonnet-4-6`

| Metric | with-skill | without-skill | Delta |
|--------|-----------|---------------|-------|
| Pass rate | 98% ± 6% | 71% ± 33% | **+26%** |
| Min / Max | 80% / 100% | 0% / 100% | |
| Time (s) | ~39.7 ± 36.3 | ~44.7 ± 66.4 | -5.0 |
| Tokens | ~27,046 ± 7,954 | ~26,357 ± 14,885 | +688 |

Sonnet pass-rate delta is computed over 27 paired evals (eval 26 excluded from both sides due to contamination). Sonnet time/token statistics are computed over 7 of 27 primary runs per configuration (14 of 54 paired runs total) — evals 1, 3, 4, 11, 12, 13, 14 have real measurements; the other 21 evals have null measurements (simulated transcripts or excluded as stale pre-v1.3 data). Summary-table Delta values are computed from unrounded means, so they may differ slightly from subtracting the displayed rounded means.

### `claude-opus-4-7`

| Metric | with-skill | without-skill | Delta |
|--------|-----------|---------------|-------|
| Pass rate | 93.0% ± 13.0% | 59.0% ± 30.0% | **+34%** |
| Min / Max | 60% / 100% | 0% / 100% | |
| Time (s) | N/A | N/A | — |
| Tokens | N/A | N/A | — |

Opus per-run time and token measurements are `null` because subagent usage data was visible only in the runtime's per-task completion notifications and was not captured at the parent level. Observed wall-clock ranges from those notifications: with_skill ~30–50s and ~37–48k tokens per run; without_skill ~10–25s and ~24–28k tokens per run. The pass-rate aggregates remain fully reliable. Opus pass-rate delta is computed over 28 paired evals (eval 26 included — Opus baseline correctly resisted reading SKILL.md when prompted to handle an unsupported model value). Summary-table Delta values are computed from unrounded means, so they may differ slightly from subtracting the displayed rounded means.

The skill improves correctness on Sonnet 4.6 by **+26 percentage points** (71% → 98%) and on Opus 4.7 by **+34 percentage points** (59% → 93%). Opus's headline delta is *larger* than Sonnet's despite Opus's stronger baseline — the pattern that drives this is detailed in the per-eval discussion below: 11 evals are newly discriminating or strengthened on Opus where Sonnet's baseline was either coincidentally hitting skill-defined phrasing (so the assertion mistakenly passed) or was harness-masked (eval 1). 2 evals collapsed on Opus (13, 21) where the base model has internalized skill behaviors. 8 evals are non-discriminating on Opus 4.7. See **Known Eval Limitations** below.

## Per-Eval Results

Each row shows passed/total per (model, configuration). Cells in **bold** are 100%; non-bold cells indicate the assertion set caught at least one failure. Cells where Opus 4.7 with-skill matches without-skill (delta = 0) are flagged in **Known Eval Limitations** below as candidates for purpose-refresh follow-up.

| # | Eval | Sonnet 4.6 With | Sonnet 4.6 Without | Opus 4.7 With | Opus 4.7 Without |
|---|------|-----------------|--------------------|---------------|------------------|
| 1 | consistency-mode-stale-step-ref | 4/5 (80%) | 4/5 (80%) | 4/5 (80%) | 1/5 (20%) |
| 2 | consistency-mode-plan-tasks-mismatch | 4/5 (80%) | 2/5 (40%) | 4/5 (80%) | 1/5 (20%) |
| 3 | argument-conflict-error | **3/3 (100%)** | **3/3 (100%)** | **3/3 (100%)** | **3/3 (100%)** |
| 4 | diff-mode-branch-review | 4/5 (80%) | 3/5 (60%) | 3/5 (60%) | 2/5 (40%) |
| 5 | copilot-json-parse | **3/3 (100%)** | 0/3 (0%) | **3/3 (100%)** | 0/3 (0%) |
| 6 | copilot-empty-findings | **2/2 (100%)** | **2/2 (100%)** | **2/2 (100%)** | 1/2 (50%) |
| 7 | copilot-malformed-json | **2/2 (100%)** | 1/2 (50%) | **2/2 (100%)** | 1/2 (50%) |
| 8 | codex-not-found | **3/3 (100%)** | 2/3 (67%) | **3/3 (100%)** | 2/3 (67%) |
| 9 | gemini-not-found | **3/3 (100%)** | 2/3 (67%) | **3/3 (100%)** | 2/3 (67%) |
| 10 | gemini-no-findings | **3/3 (100%)** | 2/3 (67%) | **3/3 (100%)** | 1/3 (33%) |
| 11 | staged-empty-warning | **3/3 (100%)** | **3/3 (100%)** | **3/3 (100%)** | **3/3 (100%)** |
| 12 | pr-target-context | **5/5 (100%)** | **5/5 (100%)** | 4/5 (80%) | 3/5 (60%) |
| 13 | focus-option | **3/3 (100%)** | 1/3 (33%) | 2/3 (67%) | 2/3 (67%) |
| 14 | apply-skip | **2/2 (100%)** | **2/2 (100%)** | **2/2 (100%)** | **2/2 (100%)** |
| 15 | triage-skips-false-positive | **3/3 (100%)** | 0/3 (0%) | **3/3 (100%)** | 0/3 (0%) |
| 16 | triage-all-skipped | **3/3 (100%)** | 1/3 (33%) | **3/3 (100%)** | 2/3 (67%) |
| 17 | triage-not-on-self-path | **3/3 (100%)** | **3/3 (100%)** | **3/3 (100%)** | **3/3 (100%)** |
| 18 | triage-user-includes-skipped | **2/2 (100%)** | **2/2 (100%)** | **2/2 (100%)** | 1/2 (50%) |
| 19 | rescan-offered-after-apply | **3/3 (100%)** | 1/3 (33%) | **3/3 (100%)** | 1/3 (33%) |
| 20 | rescan-not-offered-after-skip | **3/3 (100%)** | **3/3 (100%)** | **3/3 (100%)** | **3/3 (100%)** |
| 21 | both-staged-and-unstaged-prompt | **3/3 (100%)** | 1/3 (33%) | **3/3 (100%)** | **3/3 (100%)** |
| 22 | unstaged-only-auto-review | **3/3 (100%)** | **3/3 (100%)** | **3/3 (100%)** | 2/3 (67%) |
| 23 | staged-explicit-bypasses-detection | **3/3 (100%)** | **3/3 (100%)** | **3/3 (100%)** | 2/3 (67%) |
| 24 | rescan-y-response | **4/4 (100%)** | **4/4 (100%)** | 3/4 (75%) | 2/4 (50%) |
| 25 | pr-url-output | **4/4 (100%)** | **4/4 (100%)** | **4/4 (100%)** | 2/4 (50%) |
| 26 | unsupported-model-error | N/A | N/A | **3/3 (100%)** | 2/3 (67%) |
| 27 | branch-not-found-error | **3/3 (100%)** | **3/3 (100%)** | **3/3 (100%)** | **3/3 (100%)** |
| 28 | submodel-splitting | **3/3 (100%)** | 2/3 (67%) | 2/3 (67%) | 1/3 (33%) |

## Known Eval Limitations

### Non-discriminating evals on Opus 4.7

Of the 28 evals, 8 are non-discriminating on Opus 4.7 (with-skill = without-skill pass rate). These are candidates for future purpose-refresh work analogous to spec 25's `learn` refresh — the base model has internalized enough of the skill's behaviors that the assertions no longer differentiate.

Non-discriminating on Opus 4.7:
- Eval 3 (`argument-conflict-error`)
- Eval 11 (`staged-empty-warning`)
- Eval 13 (`focus-option`)
- Eval 14 (`apply-skip`)
- Eval 17 (`triage-not-on-self-path`)
- Eval 20 (`rescan-not-offered-after-skip`)
- Eval 21 (`both-staged-and-unstaged-prompt`)
- Eval 27 (`branch-not-found-error`)

### Collapsed evals (Sonnet discriminated, Opus does not)

2 evals discriminated on Sonnet 4.6 but collapsed to non-discriminating on Opus 4.7:
- Eval 13 (`focus-option`) — Sonnet Δ +67% → Opus Δ 0%
- Eval 21 (`both-staged-and-unstaged-prompt`) — Sonnet Δ +67% → Opus Δ 0%

These reflect Opus's stronger natural reasoning — the base model figured out the skill-defined behavior without needing the skill (eval 21: handling of both-staged-and-unstaged-changes; eval 13: focus-line surfacing was lost in inline-review harness flow). Note that eval 13's collapse is bidirectional: Opus baseline rose to 67% (from Sonnet's 33% — base model surfaces both findings naturally) AND Opus with-skill dropped to 67% (from Sonnet's 100% — focus-line construction was not visible in the inlined transcript). Both directions converge at 67%.

### Harness constraint (sub-subagents unavailable)

Eval-executor subagents cannot spawn sub-subagents (Agent tool unavailable). For evals where the skill prescribes delegating to a fresh-context reviewer subagent (1, 2, 4), the subagent-spawn assertion fails in both configurations on both models. In production, the skill correctly delegates. This is an eval-harness constraint, not a skill defect. Eval 1's harness mask was the reason its Sonnet baseline pass rate landed at 0.80 (it accidentally passed 4/5 by inference); the Opus baseline produces a more natural review without skill-defined behaviors and lands at 0.20 — revealing the underlying +0.60 discrimination.

### Eval 26 contamination handling

Eval 26 (unsupported-model-error) was contaminated on Sonnet 4.6 — the without_skill executor read `skills/peer-review/SKILL.md` from the filesystem and reproduced the skill-defined error message. Both Sonnet sides are nulled in `runs[]` and excluded from Sonnet's `run_summary_by_model` aggregates (Sonnet paired-eval count = 27). On Opus 4.7, the without_skill executor correctly resisted reading SKILL.md when given an explicit prohibition prompt; eval 26 ran cleanly on Opus (Opus paired-eval count = 28).

### Sparse Sonnet 4.6 time/token coverage

Sonnet primary-run time and token statistics are computed over 7 of 27 paired primary runs (evals 1, 3, 4, 11, 12, 13, 14 — real-execution evals). The other 21 paired evals use simulated transcripts or were excluded as stale pre-v1.3 data; their measurements are null.

### Opus 4.7 time/token measurement gap

Opus per-run time and token measurements are null because subagent usage data was visible only in transient task-completion notifications during the spec 27 run and was not captured at the parent level. Observed wall-clock and token ranges from those notifications are documented in the Summary section above. The pass-rate aggregates remain fully reliable; the time/token aggregates are the gap to close in a future re-run.

## Per-Eval Discussion

### Eval 1 — `consistency-mode-stale-step-ref`
**Scenario**: Fixture directory with SKILL.md and reference.md. SKILL.md references "Step 3 of reference.md" for the field mapping table, but reference.md has no Step 3 — the field mapping table is at Step 4.

| Configuration | Sonnet 4.6 | Opus 4.7 |
|---------------|-----------|----------|
| with-skill    | 4/5 (80%) | 4/5 (80%) |
| without-skill    | 4/5 (80%) | 1/5 (20%) |

**Zero-delta (0.80/0.80) due to eval harness constraint**. Both configurations correctly identify consistency mode and find the stale step reference. The sole failing assertion in both — "spawns a subagent" — fails because the Agent tool is not available inside eval executor subagents. In production, with-skill delegates to a fresh subagent while the baseline reviews inline.

### Eval 2 — `consistency-mode-plan-tasks-mismatch`
**Scenario**: plan.md + tasks.md fixture pair. plan.md defines --dry-run, --verbose, and --target ENV; tasks.md only covers --target and --dry-run — --verbose is missing entirely. In v1.3, spec mode was removed; plan.md+tasks.md directories now use consistency mode like any other path target.

| Configuration | Sonnet 4.6 | Opus 4.7 |
|---------------|-----------|----------|
| with-skill    | 4/5 (80%) | 4/5 (80%) |
| without-skill    | 2/5 (40%) | 1/5 (20%) |

**Discriminating** (+0.40 delta). Re-run in v1.4 with updated v1.3 assertions. with-skill correctly enters consistency mode, finds the --verbose gap, groups findings by severity, and presents the standard apply prompt. without-skill finds the --verbose gap and groups findings, but fails to enter an explicitly named consistency mode and presents a prose "Apply Prompt" section rather than the standard numbered selection format. The "spawns subagent" assertion fails in both configurations due to eval harness constraint.

### Eval 3 — `argument-conflict-error`
**Scenario**: `/peer-review --staged skills/peer-review/SKILL.md` — both `--staged` and a file path provided simultaneously. These are mutually exclusive targets.

| Configuration | Sonnet 4.6 | Opus 4.7 |
|---------------|-----------|----------|
| with-skill    | **3/3 (100%)** | **3/3 (100%)** |
| without-skill    | **3/3 (100%)** | **3/3 (100%)** |

**Non-discriminating**. Both configurations correctly detect the mutually exclusive target conflict, output an appropriate error message, and exit without running a review. Conflict detection logic is simple enough for a capable baseline to handle correctly. Establishes baseline behavior only.

### Eval 4 — `diff-mode-branch-review`
**Scenario**: `/peer-review --branch specs/16-peer-review` — diff mode review of the peer-review implementation branch vs main.

| Configuration | Sonnet 4.6 | Opus 4.7 |
|---------------|-----------|----------|
| with-skill    | 4/5 (80%) | 3/5 (60%) |
| without-skill    | 3/5 (60%) | 2/5 (40%) |

**Discriminating** (+0.20 delta). Failing assertions for without-skill:
- **Diff mode not declared explicitly**: without-skill ran a git diff review without naming it as diff mode (as distinct from spec or consistency mode).
- **Subagent not spawned**: inline review with 45 tool calls vs 8 for with-skill. without-skill spent 191.9s and 59,648 tokens; with-skill spent 105.5s and 44,948 tokens.

The subagent assertion also fails for with-skill (harness constraint), so net delta is +0.20.

### Eval 5 — `copilot-json-parse`
**Scenario**: `/peer-review --staged --model copilot` with a fixture copilot JSON response containing two findings with severities `high` and `low`. The skill must normalize these to `critical` and `minor` respectively.

| Configuration | Sonnet 4.6 | Opus 4.7 |
|---------------|-----------|----------|
| with-skill    | **3/3 (100%)** | **3/3 (100%)** |
| without-skill    | 0/3 (0%) | 0/3 (0%) |

**Discriminating** (+1.0 delta). All 3 assertions fail without-skill — severity remapping (`high` → `critical`, `low` → `minor`) and the apply prompt are both skill-defined behaviors. Without the skill, the agent presents severity labels as-is from the JSON and does not show an apply prompt.

### Eval 6 — `copilot-empty-findings`
**Scenario**: `/peer-review --staged --model copilot` with a fixture copilot JSON response containing an empty `findings` array.

| Configuration | Sonnet 4.6 | Opus 4.7 |
|---------------|-----------|----------|
| with-skill    | **2/2 (100%)** | **2/2 (100%)** |
| without-skill    | **2/2 (100%)** | 1/2 (50%) |

**On Sonnet 4.6: non-discriminating; on Opus 4.7: discriminating (+0.50)**. Both configurations produce "No issues found." when the findings array is empty, and neither shows an apply prompt. The no-findings output is natural default behavior on Sonnet; the apply prompt is skill-defined but absent in both since there are no findings to act on. On Opus 4.7, the without_skill agent paraphrased "no findings" rather than producing the literal "No issues found." — assertion 1 catches the difference, exposing discrimination on the stronger base model.

### Eval 7 — `copilot-malformed-json`
**Scenario**: `/peer-review --staged --model copilot` with a fixture copilot response that is not valid JSON (a plain text error message).

| Configuration | Sonnet 4.6 | Opus 4.7 |
|---------------|-----------|----------|
| with-skill    | **2/2 (100%)** | **2/2 (100%)** |
| without-skill    | 1/2 (50%) | 1/2 (50%) |

**Discriminating** (+0.50 delta). The specific fallback phrase "Could not parse structured findings; showing raw output." is skill-defined and fails without-skill. Showing the raw error text is natural default behavior and passes in both configurations.

### Eval 8 — `codex-not-found`
**Scenario**: `/peer-review --staged --model codex` when the `codex` binary is absent.

| Configuration | Sonnet 4.6 | Opus 4.7 |
|---------------|-----------|----------|
| with-skill    | **3/3 (100%)** | **3/3 (100%)** |
| without-skill    | 2/3 (67%) | 2/3 (67%) |

**Discriminating** (+0.33 delta). The specific install hint `npm install -g @openai/codex` is skill-defined and fails without-skill. Detecting the missing binary and stopping without showing findings are natural behaviors that pass in both configurations.

### Eval 9 — `gemini-not-found`
**Scenario**: `/peer-review --staged --model gemini` when the `gemini` binary is absent.

| Configuration | Sonnet 4.6 | Opus 4.7 |
|---------------|-----------|----------|
| with-skill    | **3/3 (100%)** | **3/3 (100%)** |
| without-skill    | 2/3 (67%) | 2/3 (67%) |

**Discriminating** (+0.33 delta). Mirrors eval 8 — specific install hint `npm install -g @google/gemini-cli` is skill-defined and fails without-skill.

### Eval 10 — `gemini-no-findings`
**Scenario**: `/peer-review --staged --model gemini` with a fixture gemini response returning exactly `NO FINDINGS`.

| Configuration | Sonnet 4.6 | Opus 4.7 |
|---------------|-----------|----------|
| with-skill    | **3/3 (100%)** | **3/3 (100%)** |
| without-skill    | 2/3 (67%) | 1/3 (33%) |

**Discriminating** (+0.33 delta). The `## Peer Review —` header format is skill-defined and fails without-skill. Outputting "No issues found." and omitting the apply prompt pass in both configurations as natural behaviors.

### Eval 11 — `staged-empty-warning`
**Scenario**: `/peer-review --staged` when `git diff --staged` returns empty output.

| Configuration | Sonnet 4.6 | Opus 4.7 |
|---------------|-----------|----------|
| with-skill    | **3/3 (100%)** | **3/3 (100%)** |
| without-skill    | **3/3 (100%)** | **3/3 (100%)** |

**Non-discriminating**. Both configurations output "No staged changes found. Stage files with `git add` first." and exit without spawning a reviewer. The warning is simple and conventional — baseline handles it correctly without skill guidance.

### Eval 12 — `pr-target-context`
**Scenario**: `/peer-review --pr 42` with fixture PR metadata (title, body, diff). Reviewer returns NO FINDINGS.

| Configuration | Sonnet 4.6 | Opus 4.7 |
|---------------|-----------|----------|
| with-skill    | **5/5 (100%)** | 4/5 (80%) |
| without-skill    | **5/5 (100%)** | 3/5 (60%) |

**On Sonnet 4.6: non-discriminating; on Opus 4.7: discriminating (+0.20)**. On Sonnet, both configurations included PR title/body as context and produced the same output. The Sonnet without-skill agent even reproduced the skill-defined `## Peer Review — PR #42` header format. On Opus 4.7, the without_skill agent did NOT use the PR title/body as explicit reviewer context (assertion 1 fails) and the header lacked a model-identifier token (assertion 5 fails) — Opus baseline is more parsimonious about reproducing skill-defined formatting. Updated in v1.6 to add `header-model-not-literal-self` assertion (5th assertion) — both configurations pass on Sonnet since general assistants naturally substitute their own model identifier and never print literal `self`; on Opus, the baseline omitted the model token entirely.

### Eval 13 — `focus-option`
**Scenario**: `/peer-review --staged --focus security` with two findings (Critical SQL injection, Minor JSDoc).

| Configuration | Sonnet 4.6 | Opus 4.7 |
|---------------|-----------|----------|
| with-skill    | **3/3 (100%)** | 2/3 (67%) |
| without-skill    | 1/3 (33%) | 2/3 (67%) |

**On Sonnet 4.6: discriminating (+0.67); on Opus 4.7: collapsed (0)**. On Sonnet, with-skill scored 100% and without-skill scored 33%. The collapse on Opus is bidirectional: with-skill dropped to 67% (focus-line construction not visible in inlined transcript — assertion 1 fails) AND baseline rose to 67% (Opus naturally surfaces both findings without skill guidance — assertion 2 passes). Both directions converge at 67%. Sonnet failing assertions for without-skill:
- **Focus line not appended to reviewer prompt**: without-skill showed "**Focus:** security" as a presentation header but did not build a reviewer prompt at all — the focus line format ("Focus especially on security. Still report any critical findings outside this focus area.") is skill-defined.
- **Apply prompt absent**: without-skill ended with a summary table and recommendation instead of the apply prompt.

### Eval 14 — `apply-skip`
**Scenario**: User replies `skip` after the skill presents two findings.

| Configuration | Sonnet 4.6 | Opus 4.7 |
|---------------|-----------|----------|
| with-skill    | **2/2 (100%)** | **2/2 (100%)** |
| without-skill    | **2/2 (100%)** | **2/2 (100%)** |

**Non-discriminating**. Both configurations output a skip summary without making file edits. The skill-defined exact phrasing ("Skipped 2 findings. No changes made.") was not reproduced by without-skill ("No changes applied..."), but the assertion accepts equivalent summaries, so both pass. Establishes baseline behavior for the skip path.

### Eval 15 — `triage-skips-false-positive`
**Scenario**: `/peer-review --model copilot` with 2 normalized findings. Triage subagent classifies Finding 1 as recommend and Finding 2 ("Install hint is legacy") as skip — the reviewed content already uses the flagged install command as the correct hint, so the finding contradicts verified content.

| Configuration | Sonnet 4.6 | Opus 4.7 |
|---------------|-----------|----------|
| with-skill    | **3/3 (100%)** | **3/3 (100%)** |
| without-skill    | 0/3 (0%) | 0/3 (0%) |

**Discriminating** (+1.0 delta). All 3 assertions fail without-skill: no "Triage filtered" section, no formal recommended/skipped separation, and no S-prefix apply prompt. With-skill correctly applies triage classification, presents Finding 2 in the filtered section (S1), and uses the triage form of the apply prompt.

### Eval 16 — `triage-all-skipped`
**Scenario**: `/peer-review --model gemini` with 2 findings. Both are low-confidence style opinions; triage subagent classifies both as skip.

| Configuration | Sonnet 4.6 | Opus 4.7 |
|---------------|-----------|----------|
| with-skill    | **3/3 (100%)** | **3/3 (100%)** |
| without-skill    | 1/3 (33%) | 2/3 (67%) |

**Discriminating** (+0.67 delta). without-skill still offered an apply prompt ("Would you like me to apply either of these anyway?") and did not output "No issues recommended." — the all-skipped path and its specific phrasing are skill-defined. The triage summary content appeared in prose (satisfying assertion 3 loosely), but the required phrase and suppressed apply prompt both fail.

### Eval 17 — `triage-not-on-self-path`
**Scenario**: `/peer-review --staged` (default `self` model) with 2 findings from the internal reviewer instance.

| Configuration | Sonnet 4.6 | Opus 4.7 |
|---------------|-----------|----------|
| with-skill    | **3/3 (100%)** | **3/3 (100%)** |
| without-skill    | **3/3 (100%)** | **3/3 (100%)** |

**Non-discriminating**. This is a regression guard: without-skill naturally produces no "Triage filtered" section (it has no concept of triage), uses a standard apply prompt without S-numbers, and lists both findings. Establishes that the self/Claude path never activates triage.

### Eval 18 — `triage-user-includes-skipped`
**Scenario**: Triage apply step — 1 recommended finding (1) and 1 skipped finding (S1). User replies `S1`.

| Configuration | Sonnet 4.6 | Opus 4.7 |
|---------------|-----------|----------|
| with-skill    | **2/2 (100%)** | **2/2 (100%)** |
| without-skill    | **2/2 (100%)** | 1/2 (50%) |

**On Sonnet 4.6: non-discriminating; on Opus 4.7: discriminating (+0.50)**. On Sonnet, the `S1` selection is literal enough that a general assistant interprets it correctly and applies only S1 without skill guidance. On Opus 4.7, the without_skill agent pivoted to asking for confirmation rather than reporting S1 as applied (assertion 1 fails) — Opus's stronger judgment second-guesses overriding the triage-filtered classification. Verifies S-prefix selection logic is working on both models, but the apply-without-confirmation behavior is skill-defined enough to discriminate on the more cautious base model.

### Eval 19 — `rescan-offered-after-apply`
**Scenario**: User replies `all` to the apply prompt. One finding applied, modifying docs/SKILL.md. Post-apply re-scan offer expected.

| Configuration | Sonnet 4.6 | Opus 4.7 |
|---------------|-----------|----------|
| with-skill    | **3/3 (100%)** | **3/3 (100%)** |
| without-skill    | 1/3 (33%) | 1/3 (33%) |

**Discriminating** (+0.67 delta). without-skill applied the finding and output an applied summary but did not offer a re-scan — it ended with "Let me know if you'd like me to review any other files." The re-scan offer and stop-generating behavior are both skill-defined behaviors absent in the baseline.

### Eval 20 — `rescan-not-offered-after-skip`
**Scenario**: User replies `skip` to the apply prompt.

| Configuration | Sonnet 4.6 | Opus 4.7 |
|---------------|-----------|----------|
| with-skill    | **3/3 (100%)** | **3/3 (100%)** |
| without-skill    | **3/3 (100%)** | **3/3 (100%)** |

**Non-discriminating**. Both configurations output the skip summary and produce no re-scan offer — baseline naturally skips applying and makes no edits when told to skip. Verifies re-scan suppression on the skip path.

### Eval 21 — `both-staged-and-unstaged-prompt`
**Scenario**: `/peer-review` (no target) with both staged and unstaged changes present (one file each). Skill should detect both and prompt the user to choose which to review.

| Configuration | Sonnet 4.6 | Opus 4.7 |
|---------------|-----------|----------|
| with-skill    | **3/3 (100%)** | **3/3 (100%)** |
| without-skill    | 1/3 (33%) | **3/3 (100%)** |

**On Sonnet 4.6: discriminating (+0.67); on Opus 4.7: collapsed (0)**. On Sonnet, the disambiguation prompt ("You have both staged and unstaged changes. Review which? [staged/unstaged/all]") is entirely skill-defined — Sonnet without-skill silently reviewed both files without asking, missing both the prompt and the stop-before-reviewer requirement. On Opus 4.7, the baseline naturally produced an equivalent disambiguation prompt and stopped before reviewing, fully matching skill behavior — Opus's stronger reasoning derived the same handling without the skill, collapsing the eval to 100%/100%.

### Eval 22 — `unstaged-only-auto-review`
**Scenario**: `/peer-review` (no target) with no staged changes but unstaged changes present. Reviewer returns NO FINDINGS.

| Configuration | Sonnet 4.6 | Opus 4.7 |
|---------------|-----------|----------|
| with-skill    | **3/3 (100%)** | **3/3 (100%)** |
| without-skill    | **3/3 (100%)** | 2/3 (67%) |

**On Sonnet 4.6: non-discriminating; on Opus 4.7: discriminating (+0.33)**. On Sonnet, auto-reviewing unstaged changes when nothing is staged is intuitive enough that both configurations handle it correctly — Sonnet baseline included a note ("No changes are currently staged — reviewing those instead.") AND reproduced the literal "No issues found." phrase without skill guidance. On Opus 4.7, the without_skill agent paraphrased "no findings" rather than producing the literal "No issues found." (assertion 3 fails) — same pattern as eval 6 and eval 23.

### Eval 23 — `staged-explicit-bypasses-detection`
**Scenario**: `/peer-review --staged` with both staged and unstaged changes present. Explicit --staged should skip auto-detection and review staged only.

| Configuration | Sonnet 4.6 | Opus 4.7 |
|---------------|-----------|----------|
| with-skill    | **3/3 (100%)** | **3/3 (100%)** |
| without-skill    | **3/3 (100%)** | 2/3 (67%) |

**On Sonnet 4.6: non-discriminating; on Opus 4.7: discriminating (+0.33)**. Using `--staged` as a flag to scope review to staged changes only is intuitive — Sonnet baseline correctly excluded the unstaged file and noted it was out of scope, AND reproduced the literal "No issues found." phrase. On Opus 4.7, the without_skill agent paraphrased "no findings" rather than producing the literal phrase (assertion 3 fails) — same pattern as eval 6 and eval 22. The internal distinction (skipping auto-detect logic) is not observable in the output on either model. Verifies explicit --staged behavior works correctly.

### Eval 24 — `rescan-y-response`
**Scenario**: Re-scan offer shown after applying one finding. User replies `y`. Re-scan reviewer returns one minor finding. Tests that re-scan uses consistency mode, no second offer is shown, and apply prompt is standard Claude-path form.

| Configuration | Sonnet 4.6 | Opus 4.7 |
|---------------|-----------|----------|
| with-skill    | **4/4 (100%)** | 3/4 (75%) |
| without-skill    | **4/4 (100%)** | 2/4 (50%) |

**On Sonnet 4.6: non-discriminating; on Opus 4.7: discriminating (+0.25)**. On Sonnet, re-scan behavior with consistency mode, suppressed second offer, and standard apply prompt is intuitive enough for a capable baseline. On Opus 4.7, both configurations failed assertion 1 (consistency mode unobserved in transcript — both with-skill and without-skill omitted explicit mode declaration); without-skill additionally failed assertion 2 (severity heading group missing — finding labeled inline as "minor" rather than under a `### Minor` heading). The eval captures this as a +0.25 delta on Opus, but the harness-driven invisibility of mode selection masks part of the with-skill discrimination.

### Eval 25 — `pr-url-output`
**Scenario**: `/peer-review --pr 55` with fixture PR data. Reviewer returns NO FINDINGS. Tests that the PR URL appears as the last line at the terminal state.

| Configuration | Sonnet 4.6 | Opus 4.7 |
|---------------|-----------|----------|
| with-skill    | **4/4 (100%)** | **4/4 (100%)** |
| without-skill    | **4/4 (100%)** | 2/4 (50%) |

**On Sonnet 4.6: non-discriminating; on Opus 4.7: discriminating (+0.50)**. On Sonnet, baseline naturally appended the PR URL and reproduced the literal "No issues found." phrase. On Opus 4.7, the without_skill agent paraphrased "no findings" (assertion 1 fails) and did NOT place the PR URL as the last line — it ended with a conversational closing sentence (assertion 2 fails). The consolidated PR URL rule in Step 6 turns out to be a discriminating differentiator on the stronger base model. Updated in v1.6 to add `header-model-not-literal-self` assertion (4th assertion) — both configurations pass on Sonnet for the same reason as eval 12; Opus passes A4 because no model token appears in its baseline header.

### Eval 26 — `unsupported-model-error`
**Scenario**: `/peer-review --staged --model gpt-4o` — unsupported model value. Tests that the skill errors with a specific message listing supported options.

| Configuration | Sonnet 4.6 | Opus 4.7 |
|---------------|-----------|----------|
| with-skill    | N/A | **3/3 (100%)** |
| without-skill    | N/A | 2/3 (67%) |

**On Sonnet 4.6: excluded from aggregates (contaminated run); on Opus 4.7: discriminating (+0.33)**. The Sonnet without_skill agent read the SKILL.md from the filesystem and reproduced the skill-defined error message. Both Sonnet sides are nulled in benchmark.json and excluded from Sonnet's run_summary mean/stddev/delta calculations. On Opus 4.7, the without_skill executor correctly resisted reading SKILL.md when given an explicit prohibition prompt — the eval ran cleanly and Opus discriminates at +0.33 (3/3 with-skill vs 2/3 without-skill). The specific phrasing ("Unsupported --model value: …. Supported external CLIs: copilot, codex, gemini.") is now confirmed skill-defined and discriminating on Opus: the Opus baseline declined to invent a specific list of supported model values without skill knowledge, failing assertion 2 (which requires self/claude-*/copilot/codex/gemini explicitly listed).

### Eval 27 — `branch-not-found-error`
**Scenario**: `/peer-review --branch feature/does-not-exist` when the branch doesn't exist. Tests that the skill errors and lists available branches.

| Configuration | Sonnet 4.6 | Opus 4.7 |
|---------------|-----------|----------|
| with-skill    | **3/3 (100%)** | **3/3 (100%)** |
| without-skill    | **3/3 (100%)** | **3/3 (100%)** |

**Non-discriminating**. Listing available branches after a not-found error is intuitive; baseline handled it correctly without skill guidance. Establishes branch-not-found handling works correctly.

### Eval 28 — `submodel-splitting`
**Scenario**: `/peer-review --staged --model copilot:gpt-4o-mini` with fixture copilot JSON returning one finding with severity `medium`. Tests colon-splitting of `--model` value and normalization of `medium` → `major`.

| Configuration | Sonnet 4.6 | Opus 4.7 |
|---------------|-----------|----------|
| with-skill    | **3/3 (100%)** | 2/3 (67%) |
| without-skill    | 2/3 (67%) | 1/3 (33%) |

**Discriminating** (+0.33 delta). Failing assertion for without_skill:
- **Severity not normalized**: without_skill presented the finding with severity `medium` as-is — the normalization rule (`medium` → `major`) is skill-defined. Matches the pattern of evals 5, 7, 8, 9, 10 where CLI output normalization discriminates. Sub-model splitting itself passed in both configurations (the `:` split and `--model` flag are intuitive); severity normalization is the differentiator.

## Notes

- **Agent tool in eval context**: eval executor subagents cannot spawn further subagents (Agent tool unavailable). For evals 1 and 4, the "spawns subagent" assertion fails in both configurations for this reason. In production use, the skill correctly delegates to a fresh subagent.
- **Evals 5–10 and 15–20 use simulated transcripts**: fixture CLI responses and triage outputs are embedded in the eval prompt rather than calling real external CLIs or spawning real triage subagents. Time and token measurements are null for these runs.
- **Evals 11–14 have real measurements**: executor subagents ran the full skill workflow; time and token data recorded.
- **Eval 6 non-discriminating**: both configurations naturally output "No issues found." for an empty findings array. This establishes baseline behavior for the empty-findings case.
- **Eval 3 redesign note**: Previously tested "no staged changes → warn and exit" (non-discriminating). Redesigned to test argument conflict (`--staged` + path → error). Also non-discriminating — conflict detection is simple enough that a capable baseline handles it correctly.
- **Delta from adding evals 11–14**: adding 4 mostly non-discriminating evals (11, 12, 14) plus one discriminating eval (13) reduced the headline delta from +31% to +27%.
- **Delta from adding evals 15–20**: adding 3 discriminating evals (15, 16, 19) and 3 non-discriminating evals (17, 18, 20) restores and exceeds the headline delta: +27% → +31%. Evals 17, 18, 20 are non-discriminating by design — they serve as regression guards or verify intuitive behaviors that pass without skill knowledge.
- **Delta from v1.3 spec-mode removal (eval 2 re-scope)**: eval 2 renamed and criteria inverted; historical pass/fail data and measurements excluded from aggregates pending re-run. Headline delta shifts from +31% to +30% (pass rate means recomputed excluding eval 2; stale time/token measurements also excluded).
- **Delta from v1.4 evals (evals 2, 21, 22, 23)**: eval 2 re-run confirms +0.40 delta. Eval 21 (both-staged-and-unstaged-prompt) adds +0.67 delta. Evals 22 and 23 are non-discriminating, diluting the headline delta from +30% to +29%.
- **Delta from v1.5 evals (evals 24–28)**: eval 28 (submodel-splitting) discriminates at +0.33. Evals 24, 25, 27 are non-discriminating. Eval 26 is contaminated (without_skill run contaminated; both with_skill and without_skill results nulled and excluded from aggregates to keep paired-eval counts consistent). Delta computed over 27 paired evals, diluting headline from +29% to +26%.
- **Evals 15–28 use simulated transcripts**: fixture CLI responses and triage/branch/reviewer outputs are embedded in eval prompts rather than calling real external systems. Time and token measurements are null for these runs.
