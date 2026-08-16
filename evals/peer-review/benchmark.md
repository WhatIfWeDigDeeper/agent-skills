# peer-review Benchmark Results

**Models tested**:
- `claude-sonnet-4-6` — primary suite 2026-04-09. Analyzer: Sonnet 4.6.
- `claude-opus-4-7` — full suite on 2026-04-25 (spec 27). Analyzer: **Sonnet 4.6** (Opus subagent rate-limit risk; Sonnet used to grade all transcripts uniformly for analyzer-model consistency, following the spec 26 precedent).
- `claude-sonnet-5` / `claude-opus-5` — targeted 3-eval re-run on 2026-08-16 (spec 58, Gemini CLI removal). **Excluded from all aggregates** — see *v1.15 re-run cohort* below.

**Evals**: 27 evals. The aggregate corpus is 24 paired evals × 2 configurations × 2 models = **96 runs** feeding `run_summary`, plus 12 nulled 4-6/4-7 runs (evals 9, 16, 26) and 12 excluded v1.15 cohort runs, for **120 entries** in `runs[]`. All `run_number == 1`.

Three exclusions apply to the 24-eval aggregate. Eval 26 (`unsupported-model-error`) was contaminated on Sonnet 4.6 (that executor read SKILL.md from the filesystem). Evals 9, 16, and 26 all changed semantics in v1.15 when the Gemini CLI route was removed, so their 4-6/4-7 result fields and expectation verdicts are nulled. Eval 10 (`gemini-no-findings`) was deleted outright; IDs are **not** renumbered, so the sequence gaps at 10.

**Skill version**: v1.7. Sonnet 4.6 runs were produced under v1.6 (current as of 2026-04-09); Opus 4.7 runs under v1.7. The v1.15 cohort does not move `metadata.skill_version` because it feeds no aggregate.

## Summary

### `claude-sonnet-4-6`

| Metric | with-skill | without-skill | Delta |
|--------|-----------|---------------|-------|
| Pass rate | 97% ± 7% | 73% ± 34% | **+24%** |
| Min / Max | 80% / 100% | 0% / 100% | |
| Time (s) | ~39.7 ± 36.3 | ~44.7 ± 66.4 | -5.0 |
| Tokens | ~27,046 ± 7,954 | ~26,357 ± 14,885 | +688 |

Sonnet pass-rate delta is computed over 24 paired evals (evals 9, 16, 26 nulled; eval 10 deleted). Sonnet time/token statistics are computed over 7 of 24 primary runs per configuration (14 of 48 paired runs total) — evals 1, 3, 4, 11, 12, 13, 14 have real measurements; the other 17 evals have null measurements (simulated transcripts or excluded as stale pre-v1.3 data). Summary-table Delta values are computed from unrounded means, so they may differ slightly from subtracting the displayed rounded means.

### `claude-opus-4-7`

| Metric | with-skill | without-skill | Delta |
|--------|-----------|---------------|-------|
| Pass rate | 92.0% ± 13.0% | 59.0% ± 32.0% | **+33%** |
| Min / Max | 60% / 100% | 0% / 100% | |
| Time (s) | N/A | N/A | — |
| Tokens | N/A | N/A | — |

Opus per-run time and token measurements are `null` because subagent usage data was visible only in the runtime's per-task completion notifications and was not captured at the parent level. Observed wall-clock ranges from those notifications: with_skill ~30–50s and ~37–48k tokens per run; without_skill ~10–25s and ~24–28k tokens per run. The pass-rate aggregates remain fully reliable. Opus pass-rate delta is computed over the same 24 paired evals as Sonnet — eval 26 ran cleanly on Opus (the baseline correctly resisted reading SKILL.md), but it is nulled alongside evals 9 and 16 for the v1.15 semantic change, so both models now aggregate over an identical eval set. Summary-table Delta values are computed from unrounded means, so they may differ slightly from subtracting the displayed rounded means.

The skill improves correctness on Sonnet 4.6 by **+24 percentage points** (73% → 97%) and on Opus 4.7 by **+33 percentage points** (59% → 92%). Opus's headline delta is *larger* than Sonnet's despite Opus's stronger baseline — the pattern that drives this is detailed in the per-eval discussion below: 10 of the 24 paired evals are newly discriminating or strengthened on Opus — 8 newly discriminating (1, 6, 12, 18, 22, 23, 24, 25), where Sonnet's baseline was either coincidentally hitting skill-defined phrasing (so the assertion mistakenly passed) or was harness-masked (eval 1), plus 2 (2, 28) that discriminate on both models but with a larger Opus delta. 2 evals collapsed on Opus (13, 21) where the base model has internalized skill behaviors. 8 of the 24 paired evals are non-discriminating on Opus 4.7. See **Known Eval Limitations** below.

### v1.15 re-run cohort (`claude-sonnet-5` / `claude-opus-5`)

Removing the Gemini CLI route changed the semantics of evals 9, 16, and 26, so their 4-6/4-7 measurements were nulled rather than carried forward. The 4-6/4-7 models are no longer spawnable, so the re-runs were recorded as a separate cohort:

| Eval | Sonnet 5 With | Sonnet 5 Without | Opus 5 With | Opus 5 Without |
|---|---|---|---|---|
| 9 `gemini-model-removed` | **4/4 (100%)** | 2/4 (50%) | **4/4 (100%)** | 3/4 (75%) |
| 16 `triage-all-skipped` | **3/3 (100%)** | 2/3 (67%) | **3/3 (100%)** | 2/3 (67%) |
| 26 `unsupported-model-error` | **3/3 (100%)** | 2/3 (67%) | **3/3 (100%)** | 2/3 (67%) |

These 12 runs are **excluded from `run_summary` and `run_summary_by_model`**: a 3-eval sample is too small to aggregate, mixing it into a v1.6/v1.7 corpus would misattribute the untouched runs, and every `without_skill` run is contaminated (below).

**Known contamination channel — the skill description.** Every `without_skill` run in this cohort named `copilot` and `codex` as the supported external CLIs without reading SKILL.md. The leak is the skill's own frontmatter description, which the harness injects into every subagent's system prompt via the available-skills listing ("routes to external LLM CLIs (Copilot, Codex)"). This is a *different* channel from the eval-26 Sonnet 4.6 contamination, which was a filesystem SKILL.md read — fencing the executor out of SKILL.md does not close it. It affects eval 9 most, because the repurposed eval asks precisely what the description states, and eval 26 next. The bias raises the *baseline*, so these deltas are lower bounds rather than inflated claims. The authoritative regression guard for the Gemini removal is the deterministic `TestGeminiRemoved` class in `tests/peer-review/test_model_routing.py`, not eval 9.

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
| 9 | gemini-model-removed | N/A | N/A | N/A | N/A |
| 11 | staged-empty-warning | **3/3 (100%)** | **3/3 (100%)** | **3/3 (100%)** | **3/3 (100%)** |
| 12 | pr-target-context | **5/5 (100%)** | **5/5 (100%)** | 4/5 (80%) | 3/5 (60%) |
| 13 | focus-option | **3/3 (100%)** | 1/3 (33%) | 2/3 (67%) | 2/3 (67%) |
| 14 | apply-skip | **2/2 (100%)** | **2/2 (100%)** | **2/2 (100%)** | **2/2 (100%)** |
| 15 | triage-skips-false-positive | **3/3 (100%)** | 0/3 (0%) | **3/3 (100%)** | 0/3 (0%) |
| 16 | triage-all-skipped | N/A | N/A | N/A | N/A |
| 17 | triage-not-on-self-path | **3/3 (100%)** | **3/3 (100%)** | **3/3 (100%)** | **3/3 (100%)** |
| 18 | triage-user-includes-skipped | **2/2 (100%)** | **2/2 (100%)** | **2/2 (100%)** | 1/2 (50%) |
| 19 | rescan-offered-after-apply | **3/3 (100%)** | 1/3 (33%) | **3/3 (100%)** | 1/3 (33%) |
| 20 | rescan-not-offered-after-skip | **3/3 (100%)** | **3/3 (100%)** | **3/3 (100%)** | **3/3 (100%)** |
| 21 | both-staged-and-unstaged-prompt | **3/3 (100%)** | 1/3 (33%) | **3/3 (100%)** | **3/3 (100%)** |
| 22 | unstaged-only-auto-review | **3/3 (100%)** | **3/3 (100%)** | **3/3 (100%)** | 2/3 (67%) |
| 23 | staged-explicit-bypasses-detection | **3/3 (100%)** | **3/3 (100%)** | **3/3 (100%)** | 2/3 (67%) |
| 24 | rescan-y-response | **4/4 (100%)** | **4/4 (100%)** | 3/4 (75%) | 2/4 (50%) |
| 25 | pr-url-output | **4/4 (100%)** | **4/4 (100%)** | **4/4 (100%)** | 2/4 (50%) |
| 26 | unsupported-model-error | N/A | N/A | N/A | N/A |
| 27 | branch-not-found-error | **3/3 (100%)** | **3/3 (100%)** | **3/3 (100%)** | **3/3 (100%)** |
| 28 | submodel-splitting | **3/3 (100%)** | 2/3 (67%) | 2/3 (67%) | 1/3 (33%) |

## Known Eval Limitations

### Non-discriminating evals on Opus 4.7

Of the 24 paired evals, 8 are non-discriminating on Opus 4.7 (with-skill = without-skill pass rate). Evals 9, 16, and 26 are not in either bucket — their 4.6/4.7 results are nulled. These are candidates for future purpose-refresh work analogous to spec 25's `learn` refresh — the base model has internalized enough of the skill's behaviors that the assertions no longer differentiate.

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

Eval 26 (unsupported-model-error) was contaminated on Sonnet 4.6 — the without_skill executor read `skills/peer-review/SKILL.md` from the filesystem and reproduced the skill-defined error message. On Opus 4.7, the without_skill executor correctly resisted reading SKILL.md when given the same prohibition prompt, so eval 26 ran cleanly there. Both sides on both models are now nulled anyway: v1.15 narrowed the eval's expected supported-values list, so all four 4-6/4-7 runs describe an eval that no longer exists. Paired-eval count is 24 on both models. A *third*, distinct contamination channel showed up in the v1.15 re-run — the skill description in the available-skills listing — which no SKILL.md fence can close; see the *v1.15 re-run cohort* section.

### Sparse Sonnet 4.6 time/token coverage

Sonnet primary-run time and token statistics are computed over 7 of 24 paired primary runs (evals 1, 3, 4, 11, 12, 13, 14 — real-execution evals). The other 17 paired evals use simulated transcripts or were excluded as stale pre-v1.3 data; their measurements are null.

### Opus 4.7 time/token measurement gap

Opus per-run time and token measurements are null because subagent usage data was visible only in transient task-completion notifications during the spec 27 run and was not captured at the parent level. Observed wall-clock and token ranges from those notifications are documented in the Summary section above. The pass-rate aggregates remain fully reliable; the time/token aggregates are the gap to close in a future re-run.

## Per-Eval Discussion

### Eval 1 — `consistency-mode-stale-step-ref`
**Scenario**: Fixture directory with SKILL.md and reference.md. SKILL.md references "Step 3 of reference.md" for the field mapping table, but reference.md has no Step 3 — the field mapping table is at Step 4.

| Configuration | Sonnet 4.6 | Opus 4.7 |
|---------------|-----------|----------|
| with-skill    | 4/5 (80%) | 4/5 (80%) |
| without-skill    | 4/5 (80%) | 1/5 (20%) |

**Sonnet 4.6: zero-delta (0.80/0.80) due to eval harness constraint; Opus 4.7: discriminating (0.80/0.20)**. On Sonnet, both configurations correctly identify consistency mode and find the stale step reference, so the sole failing assertion on each side is "spawns a subagent," which fails because the Agent tool is not available inside eval executor subagents. On Opus, the same harness constraint still caps the with-skill side at 4/5, but without-skill drops to 1/5, so the eval remains discriminating there. In production, with-skill delegates to a fresh subagent while the baseline reviews inline.

### Eval 2 — `consistency-mode-plan-tasks-mismatch`
**Scenario**: plan.md + tasks.md fixture pair. plan.md defines --dry-run, --verbose, and --target ENV; tasks.md only covers --target and --dry-run — --verbose is missing entirely. In v1.3, spec mode was removed; plan.md+tasks.md directories now use consistency mode like any other path target.

| Configuration | Sonnet 4.6 | Opus 4.7 |
|---------------|-----------|----------|
| with-skill    | 4/5 (80%) | 4/5 (80%) |
| without-skill    | 2/5 (40%) | 1/5 (20%) |

**Discriminating** (Sonnet +0.40; Opus +0.60). Re-run in v1.4 with updated v1.3 assertions. with-skill correctly enters consistency mode, finds the --verbose gap, groups findings by severity, and presents the standard apply prompt. without-skill finds the --verbose gap and groups findings, but fails to enter an explicitly named consistency mode and presents a prose "Apply Prompt" section rather than the standard numbered selection format. The "spawns subagent" assertion fails in both configurations due to eval harness constraint.

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

### Eval 9 — `gemini-model-removed`
**Scenario**: `/peer-review --staged --model gemini` after v1.15 removed the Gemini CLI route. Tests that `gemini` now falls through to the standard unsupported-model error, with no binary probe and no npm install hint.

Repurposed in v1.15 from `gemini-not-found`, which tested the opposite behavior (detect the missing `gemini` binary and print `npm install -g @google/gemini-cli`). The 4-6/4-7 measurements are nulled; results below are from the v1.15 Sonnet 5 / Opus 5 cohort.

| Configuration | Sonnet 4.6 | Opus 4.7 | Sonnet 5 | Opus 5 |
|---------------|-----------|----------|----------|--------|
| with-skill    | N/A | N/A | **4/4 (100%)** | **4/4 (100%)** |
| without-skill    | N/A | N/A | 2/4 (50%) | 3/4 (75%) |

**Contaminated baseline — read the delta as a lower bound, not as evidence of skill value.** Both `without_skill` agents named `copilot` and `codex` without reading SKILL.md, taking them from the skill description in the available-skills listing (see *v1.15 re-run cohort* above). Both baselines fail the supported-options assertion only because they omit `self` and `claude-*`, which the description also omits — a description-completeness artifact, not a skill-vs-baseline difference. The Sonnet 5 baseline additionally went on to review the diff instead of exiting; the Opus 5 baseline stopped, which is the whole of its 75%-vs-50% edge. The real regression guard for this removal is `TestGeminiRemoved` in `tests/peer-review/test_model_routing.py`.

Eval 10 (`gemini-no-findings`) was deleted in v1.15 — its coverage (the `## Peer Review —` header format on an empty-findings CLI response) duplicates eval 6 (`copilot-empty-findings`). IDs are not renumbered, so the sequence gaps at 10.

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

**On Sonnet 4.6: non-discriminating; on Opus 4.7: discriminating (+0.20)**. On Sonnet, both configurations included PR title/body as context and produced the same output. The Sonnet without-skill agent even reproduced the skill-defined `## Peer Review — PR #42` header format. On Opus 4.7, the with_skill agent did NOT include PR title/body as explicit reviewer context — its transcript showed only the header and `No issues found.` (assertion 1 fails). The Opus without_skill agent did include PR title/body, but produced `NO FINDINGS.` instead of the literal `No issues found.` (assertion 3 fails) and its header lacked a model-identifier token (assertion 5 fails). Updated in v1.6 to add `header-model-not-literal-self` assertion (5th assertion) — both configurations pass on Sonnet since general assistants naturally substitute their own model identifier and never print literal `self`; on Opus, the baseline omitted the model token entirely.

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
**Scenario**: `/peer-review --model copilot` with 2 findings. Both are low-confidence style opinions; triage subagent classifies both as skip.

Re-pointed in v1.15 from `--model gemini` to `--model copilot` — gemini was only the vehicle for reaching the triage path, and copilot matches the simulated-CLI pattern already used by evals 5, 6, 7, 15, and 28. The 4-6/4-7 measurements are nulled; results below are from the v1.15 Sonnet 5 / Opus 5 cohort. Consequence: copilot now carries triage coverage for evals 15 **and** 16, and the codex triage path is intentionally uncovered.

| Configuration | Sonnet 4.6 | Opus 4.7 | Sonnet 5 | Opus 5 |
|---------------|-----------|----------|----------|--------|
| with-skill    | N/A | N/A | **3/3 (100%)** | **3/3 (100%)** |
| without-skill    | N/A | N/A | 2/3 (67%) | 2/3 (67%) |

**Discriminating** (+0.33 on both Sonnet 5 and Opus 5). Neither baseline emitted the literal "No issues recommended." — the all-skipped path and its specific phrasing are skill-defined. Both baselines did suppress the apply prompt and did produce a per-finding skip summary in prose, so only the literal-phrase assertion fails. The graders flagged mild contamination here (both baselines reproduce the skill's triage/skip vocabulary), but the discriminating assertion is a literal string the description never mentions.

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

Narrowed in v1.15: the expected supported-values list dropped `gemini`, so the 4-6/4-7 measurements are nulled. Results below are from the v1.15 Sonnet 5 / Opus 5 cohort.

| Configuration | Sonnet 4.6 | Opus 4.7 | Sonnet 5 | Opus 5 |
|---------------|-----------|----------|----------|--------|
| with-skill    | N/A | N/A | **3/3 (100%)** | **3/3 (100%)** |
| without-skill    | N/A | N/A | 2/3 (67%) | 2/3 (67%) |

**Discriminating** (+0.33 on both Sonnet 5 and Opus 5), **with a contaminated baseline**. The specific phrasing ("Unsupported --model value: …. Supported external CLIs: copilot, codex.") is skill-defined, and both baselines fail assertion 2 — but only narrowly: each named `copilot` and `codex` correctly from the skill description in the available-skills listing and failed solely on the missing `self` / `claude-*` entries. Historically this eval was nulled on Sonnet 4.6 for a *different* contamination — that executor read `skills/peer-review/SKILL.md` from the filesystem — while Opus 4.7 ran cleanly; both are now superseded by the v1.15 re-run.

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

**Discriminating** (+0.33 delta). Failing assertions differed by model/configuration:
- **Severity not normalized in without_skill runs**: baseline output presented the finding with severity `medium` as-is rather than applying the skill-defined normalization (`medium` → `major`). This matches the pattern of evals 5, 7, 8, 9, 10 where CLI output normalization discriminates.
- **Sub-model splitting was not uniformly correct across models**: Sonnet with-skill passed all 3 assertions, but Opus with-skill finished 2/3 because the submodel-flag/argument behavior still failed there. So the eval's delta is not attributable solely to severity normalization; it reflects both normalization differences and model-specific reliability on the `--model provider:model` handling.

## Notes

### General (both models)

- **Agent tool in eval context**: eval executor subagents cannot spawn further subagents (Agent tool unavailable). For evals 1, 2, and 4, the "spawns subagent" assertion fails in both configurations for this reason. In production use, the skill correctly delegates to a fresh subagent.
- **Eval 3 redesign note**: Previously tested "no staged changes → warn and exit" (non-discriminating). Redesigned to test argument conflict (`--staged` + path → error). Also non-discriminating on both models — conflict detection is simple enough that a capable baseline handles it correctly.
- **Simulated-transcript fixtures**: evals 5–9 and 15–28 embed fixture CLI/triage/branch/reviewer outputs in the eval prompt rather than calling real external systems. The fixture design is the same on both models.
- **v1.15 — Gemini CLI route removed (spec 58)**: Google discontinued `@google/gemini-cli` in favor of the Antigravity IDE, so `--model gemini` was removed rather than left to rot; it now falls through to the standard `Unsupported --model value:` error. Eval impact: eval 10 (`gemini-no-findings`) deleted as duplicative of eval 6; eval 9 repurposed from `gemini-not-found` to `gemini-model-removed` as the regression pin; eval 16 re-pointed from `--model gemini` to `--model copilot`; eval 26's supported-values list narrowed. All three surviving evals had their 4-6/4-7 results nulled and were re-run on a Sonnet 5 / Opus 5 cohort that is excluded from every aggregate. Headline deltas moved from +26%/+34% to **+24% (Sonnet 4.6) / +33% (Opus 4.7)** over 24 paired evals — the change is entirely composition (which evals are counted), not a behavior regression. The deterministic guard for the removal is `TestGeminiRemoved` in `tests/peer-review/test_model_routing.py`.
- **v1.13 — no-behavior-change size refactor (702 → 381 lines, -46%)**: spec 45 split the four heaviest branch-specific blocks (secret-scan mechanics, prompt templates, external-CLI invocations, output templates) into `skills/peer-review/references/` behind imperative handoffs. The full suite was **not** re-benchmarked — per `evals/CLAUDE.md`, structural refactors that move logic to reference files run only a targeted parity check. Parity was validated deterministically: every moved block (secret-scan bash, copilot/codex/gemini invocations + cleanup, both prompt bodies, the 4e parse + severity table) is **byte-identical** to the `origin/main` snapshot, and all 175 peer-review unit tests pass unchanged. No `benchmark.json` run entries were added and `metadata.skill_version` is unchanged (validation-only).

### Sonnet 4.6

- **Time/token measurements**: 7 of 24 paired evals (1, 3, 4, 11, 12, 13, 14) have non-null measurements (executor subagents ran the full skill workflow). All other evals are null — most for the simulated-transcript reason above; eval 2 measurements were excluded as stale pre-v1.3 data.
- **Discriminating evals**: 10 of the 24 paired evals discriminate on Sonnet 4.6 (2, 4, 5, 7, 8, 13, 15, 19, 21, 28).
- **Eval 6 (`copilot-empty-findings`)**: non-discriminating on Sonnet — both configurations naturally output "No issues found." for an empty findings array.
- **Delta from adding evals 11–14**: adding 4 mostly non-discriminating evals (11, 12, 14) plus one discriminating eval (13) reduced the headline delta from +31% to +27%.
- **Delta from adding evals 15–20**: adding 3 discriminating evals (15, 16, 19) and 3 non-discriminating evals (17, 18, 20) restores and exceeds the headline delta: +27% → +31%. Evals 17, 18, 20 are non-discriminating by design — they serve as regression guards or verify intuitive behaviors that pass without skill knowledge.
- **Delta from v1.3 spec-mode removal (eval 2 re-scope)**: eval 2 renamed and criteria inverted; historical pass/fail data and measurements excluded from aggregates pending re-run. Headline delta shifts from +31% to +30% (pass rate means recomputed excluding eval 2; stale time/token measurements also excluded).
- **Delta from v1.4 evals (evals 2, 21, 22, 23)**: eval 2 re-run confirms +0.40 delta. Eval 21 (both-staged-and-unstaged-prompt) adds +0.67 delta. Evals 22 and 23 are non-discriminating, diluting the headline delta from +30% to +29%.
- **Delta from v1.5 evals (evals 24–28)**: eval 28 (submodel-splitting) discriminates at +0.33. Evals 24, 25, 27 are non-discriminating. Eval 26 is contaminated (without_skill run contaminated; both with_skill and without_skill results nulled and excluded from aggregates to keep paired-eval counts consistent). Delta was computed over 27 paired evals at the time, diluting headline from +29% to +26%; v1.15 later nulled evals 9 and 16 as well and deleted eval 10, moving the Sonnet headline to +24% over 24 paired evals.

### Opus 4.7

- **Time/token measurements**: null across **all** evals — the Opus runs were graded from preserved transcripts without re-capturing parent-level time/token usage. See the per-eval table for which evals have measurements on Sonnet.
- **Eval 6 (`copilot-empty-findings`)**: discriminating on Opus 4.7 (+0.50). The without_skill agent paraphrases "no findings" rather than producing the literal "No issues found." — assertion 1 catches the difference. Discrimination appears on the stronger base model where Sonnet's baseline already matched the literal string.
