# Spec 26: pr-comments — dual-model benchmarking (Sonnet 4.6 + Opus 4.7)

## Context

The `pr-comments` skill is currently benchmarked only on `claude-sonnet-4-6` (see `evals/pr-comments/benchmark.json` — `metadata.executor_model: "claude-sonnet-4-6"`, 38 evals, +66 pp pass-rate delta). Meanwhile, the `learn` skill gained dual-model benchmarking in spec 25 (`specs/25-learn-purpose-refresh/`), establishing a canonical multi-model schema: `metadata.models_tested[]`, per-run `executor_model`, `run_summary_by_model`, and a per-model prose structure in `benchmark.md`.

Adding Opus 4.7 to `pr-comments` serves two purposes:

1. **Publish per-model deltas** so the README's `Eval Δ` column and the skill-notes `Eval cost` bullet reflect both production models, matching the reporting standard the `learn` skill now sets.
2. **Surface non-discriminating evals on Opus 4.7.** When `learn` was benchmarked on Opus 4.7, 19 of 20 cells stopped discriminating — the base model had internalized the skill's behaviors. If `pr-comments` shows a similar pattern, that signal should be visible to plan a future refresh spec (analogous to spec 25's purpose refresh of `learn`). This spec reports the signal; it does **not** rewrite the skill or add new evals.

**Scope deliberately narrower than spec 25.** Spec 25 bundled dual-model benchmarking with a skill rewrite and four new evals. This spec is dual-model benchmarking only. Skill rewrites and new evals — if warranted by Opus 4.7 results — are a follow-up spec.

## Design

### Schema changes (from `evals/learn/benchmark.json`)

Mirror the learn benchmark's multi-model schema:

- `metadata.models_tested[]`: array with one block per model. Each block carries that model's `executor_model`, `analyzer_model`, `timestamp`, `runs_per_configuration`, and `notes`.
- Per-run `executor_model` field on every entry in `runs[]` — existing Sonnet runs get `"claude-sonnet-4-6"`; new Opus runs get `"claude-opus-4-7"`.
- `run_summary_by_model` keyed by model name, each containing `pass_rate`, `time_seconds`, `tokens` with `mean`/`stddev`/`min`/`max`, plus a `delta` section comparing `with_skill` vs `without_skill` for that model.
- Top-level `metadata.executor_model` flips to the latest model (`claude-opus-4-7`) once Opus runs land — latest-model convention from `learn`. Top-level `analyzer_model` reflects the actual analyzer used by the latest-model row; in this spec that turned out to be `claude-sonnet-4-6` because Opus 4.7 hit its rate limit mid-grading and Sonnet was used to grade all 76 transcripts uniformly.
- Top-level `run_summary` mirrors the latest-model stats (Opus), so single-model consumers still read correct values for the model the skill now targets.

### Run plan

- **38 evals × 2 configurations × 1 new model = 76 new Opus 4.7 runs** (primary pass).
- **Regression runs stay Sonnet-only.** The existing `benchmark.json` has six evals with `run_number > 1` (evals 12, 14, 20, 22, 23, 24) — variance probes added for Sonnet 4.6 specifically. They are not canonical baselines. Document in `benchmark.md` "Known Eval Limitations" that Opus 4.7 runs only `run_number: 1`.
- **Existing Sonnet 4.6 runs are not re-run.** They stay as-is (schema-upgraded in Phase 1 to gain per-run `executor_model`). Sparse time/token coverage on the Sonnet side carries over (time has 11 of 76 primary runs measured, tokens has 8 of 76) — flagged in benchmark.md, not filled in.
- **Opus runs instrument time/tokens/tool_calls fully.** Don't inherit the sparse-measurement pattern; per-model Summary tables in `benchmark.md` require complete Opus stats.
- **Discrimination gate does not apply.** Unlike spec 25, no evals are dropped based on Opus results. Non-discriminating evals on Opus are a finding recorded in benchmark.md, not an action item for this spec.

### Interaction with the existing grading artifact files

`evals/pr-comments/` contains a handful of committed grading JSONs (`grading-eval37-with.json`, `grading-eval37-without.json`, `grading-eval38-*.json`, `grading-scenario-26-without-skill.json`). These are Sonnet 4.6-era audit artifacts, not part of the canonical benchmark. They are out of scope — do not generate parallel Opus versions.

## Files to Modify

| File | Change |
|---|---|
| `evals/pr-comments/benchmark.json` | Schema upgrade to multi-model (Phase 1) → append 76 Opus 4.7 run entries (Phase 4) → recompute `run_summary` and `run_summary_by_model` |
| `evals/pr-comments/benchmark.md` | Restructure Summary tables to per-model format; update Per-Eval Results table to 4-column (Sonnet with/without, Opus with/without); add "Models tested" header line with date ranges; update "Known Eval Limitations" to cover non-discriminating Opus cells and Sonnet-only regression runs |
| `README.md` | Update pr-comments `Eval Δ` column to per-model format (e.g., `+66% Sonnet 4.6 / +N% Opus 4.7`); update pr-comments Skill Notes `Eval cost` bullet with per-model time / token / delta stats |
| `cspell.config.yaml` | Add any new unknown words surfaced by cspell sweep |

No changes to `skills/pr-comments/SKILL.md` (no skill rewrite), `evals/pr-comments/evals.json` (no new evals), or the committed grading artifact files.

## Key Reference Files

- `evals/learn/benchmark.json` — schema template for `models_tested[]`, per-run `executor_model`, `run_summary_by_model`
- `evals/learn/benchmark.md` — prose template for per-model Summary tables and 4-column Per-Eval Results
- `specs/25-learn-purpose-refresh/plan.md` and `tasks.md` — execution pattern
- `evals/CLAUDE.md` — benchmarking conventions (sample stddev, 2dp pass-rate delta, `null` for unrecorded stats, `eval_name` on every run, `grading.json` shape)
- `README.md` learn row — reference format for per-model `Eval Δ` column

## Branch and Worktree

- Branch: `evals/pr-comments-opus-4-7-multi-model` (mirrors the learn branch naming `evals/learn-opus-4-7-multi-model`).
- Worktree location: `.claude/worktrees/spec-26-pr-comments-dual-model`. All edits, commits, and the benchmark runs happen in the worktree; main repo is untouched until merge.
- Agents spawned with `isolation: "worktree"` must set `WT=$(git rev-parse --show-toplevel)` and prefix all Read/Edit paths with `$WT/...` (per CLAUDE.md sandbox-workarounds rule).

## Verification

1. `python3 -c 'import json; json.load(open("evals/pr-comments/benchmark.json"))'` — valid JSON.
2. Every entry in `runs[]` has `executor_model` populated (one of `claude-sonnet-4-6`, `claude-opus-4-7`).
3. Every entry in `runs[]` has `eval_name` populated (preserve existing, set on new Opus entries).
4. `metadata.models_tested[]` contains exactly two blocks (Sonnet 4.6, Opus 4.7).
5. `metadata.skill_version` matches `metadata.version` in `skills/pr-comments/SKILL.md` (currently `1.36`).
6. `run_summary_by_model["claude-sonnet-4-6"]` and `run_summary_by_model["claude-opus-4-7"]` both present; `stddev` uses sample formula (N−1); `delta.pass_rate` at 2 decimal places.
7. Top-level `run_summary` mirrors `run_summary_by_model["claude-opus-4-7"]` (latest-model convention).
8. `benchmark.md` Summary-table `±` values match `run_summary_by_model` exactly (spot-check via `jq`).
9. `benchmark.md` "Models tested" header names both models with date ranges.
10. `benchmark.md` Per-Eval Results table has 4 columns per eval row; discriminating cells bolded on the Opus side match Opus `run_summary_by_model.delta`.
11. `benchmark.md` "Known Eval Limitations" documents (a) the regression-run Sonnet-only scope, (b) any non-discriminating evals on Opus 4.7 surfaced by the run.
12. `README.md` pr-comments `Eval Δ` matches per-model deltas from `run_summary_by_model[<model>].delta.pass_rate` (rounded).
13. `README.md` pr-comments Skill Notes `Eval cost` bullet shows per-model time / tokens / pass-rate deltas.
14. `uv run --with pytest pytest tests/` — no regressions.
15. `npx cspell README.md evals/pr-comments/benchmark.md specs/26-pr-comments-dual-model-benchmark/*.md` — clean.
16. `tests/pr-comments/` still passes (this spec doesn't touch the skill logic, so no new tests expected, but existing tests must not regress).

## Risks

- **Opus 4.7 runs may show 0–1 discriminating cells.** The `pr-comments` skill encodes workflow mechanics (GraphQL thread state, timeline-comment handling, bot-polling loops) that a base model may or may not derive from a prompt. If Opus 4.7 baseline covers most of them, the spec surfaces that as a signal, does not act on it. Mitigation: frame "Known Eval Limitations" to make the follow-up direction obvious (analogous to learn's pre-refresh state that triggered spec 25).
- **Run cost.** 76 Opus 4.7 runs — non-trivial token spend. Scope is bounded to `runs_per_configuration: 1`; no variance probing on Opus. Regression runs stay Sonnet-only.
- **Sparse Sonnet 4.6 time/token data carries over.** The current benchmark has 11 of 76 primary runs with measured `time_seconds` and 8 of 76 with measured `tokens`; the rest are `null`. Opus runs were planned to be fully instrumented but ended up with `null` time/tokens at the parent-conversation level (subagent usage data was visible only in transient task-completion notifications), so the data asymmetry persists across both models. Mitigation: flag in `benchmark.md` prose — do not back-fill (out of scope; would require re-running the March/April 2026 Sonnet suite under measurement and re-instrumenting the Opus subagent harness).
- **Regression-run divergence.** Six Sonnet-only `run_number > 1` entries will remain in `runs[]` alongside the multi-model canonical set. Aggregators must filter by `run_number: 1` when computing per-model summaries. `run_summary_by_model` aggregation in task 4.5 uses only `run_number: 1` runs per model; document this rule in benchmark.md.
- **Schema upgrade of existing runs without re-running them.** Phase 1 stamps `executor_model: "claude-sonnet-4-6"` on existing entries — a purely annotative change. The benchmark data itself is untouched; only the metadata is enriched. If any existing run entry is ambiguous about its executor, audit via git blame before stamping.

## Shipping

1. Work happens on branch `evals/pr-comments-opus-4-7-multi-model` in worktree `.claude/worktrees/spec-26-pr-comments-dual-model`.
2. Execute Phases 1–7 in the worktree.
3. Stage all changes; open PR from the branch.
4. Run `/pr-comments {pr_number}` immediately after PR creation (per CLAUDE.md post-push convention).
5. Loop `/pr-comments` until no new bot feedback.
6. Run `/pr-human-guide` to annotate for human reviewers.
7. Squash-merge after human approval; delete branch; sync local main; clean up worktree directory.
