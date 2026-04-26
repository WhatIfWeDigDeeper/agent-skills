# Spec 27: peer-review — dual-model benchmarking (Sonnet 4.6 + Opus 4.7)

## Context

Prior to spec 27, the `peer-review` skill is benchmarked only on `claude-sonnet-4-6` (see the pre-spec state of `evals/peer-review/benchmark.json` — top-level `metadata.executor_model: "claude-sonnet-4-6"`, 28 evals, 56 runs, all `run_number == 1`, with-vs-without delta `+0.26` [+26 pp]). Spec 25 (`learn`) and spec 26 (`pr-comments`) established the canonical multi-model schema: `metadata.models_tested[]`, per-run `executor_model`, `run_summary_by_model`, and a per-model prose structure in `benchmark.md`.

Adding Opus 4.7 to `peer-review` serves two purposes:

1. **Publish per-model deltas** so the README's `Eval Δ` column and the skill-notes `Eval cost` bullet reflect both production models, matching the reporting standard `learn` and `pr-comments` now set.
2. **Surface non-discriminating evals on Opus 4.7.** When `learn` was benchmarked on Opus 4.7, 19 of 20 cells stopped discriminating — the base model had internalized the skill's behaviors. `pr-comments` showed a softer pattern (delta dropped from +63 to +39 pp; 9 non-discriminating Opus cells). If `peer-review` shows a similar pattern, that signal should be visible to plan a future refresh spec. This spec reports the signal; it does **not** rewrite the skill or add new evals.

**Scope deliberately narrower than spec 25.** Spec 25 bundled dual-model benchmarking with a skill rewrite and four new evals. Specs 26 and 27 are dual-model benchmarking only. Skill rewrites and new evals — if warranted by Opus 4.7 results — are a follow-up spec.

## Design

### Schema changes (from `evals/learn/benchmark.json` and `evals/pr-comments/benchmark.json`)

Mirror the multi-model schema established in specs 25 and 26:

- `metadata.models_tested[]`: array with one block per model. Each block carries that model's `executor_model`, `analyzer_model`, `timestamp`, `runs_per_configuration`, and `notes`.
- Per-run `executor_model` field on every entry in `runs[]` — existing Sonnet runs get `"claude-sonnet-4-6"`; new Opus runs get `"claude-opus-4-7"`.
- `run_summary_by_model` keyed by model name, each containing `pass_rate`, `time_seconds`, `tokens` with `mean`/`stddev`/`min`/`max`, plus a `delta` section comparing `with_skill` vs `without_skill` for that model.
- Top-level `metadata.executor_model` flips to the latest model (`claude-opus-4-7`) once Opus runs land — latest-model convention from `learn` and `pr-comments`. Top-level `analyzer_model` reflects the actual analyzer used by the latest-model row; given the spec 26 precedent (Opus rate-limited mid-grading and Sonnet was used to grade all 76 transcripts uniformly), select Sonnet 4.6 as the analyzer from the start for analyzer-uniformity and record `analyzer_model: "claude-sonnet-4-6"` on the Opus row. **Outcome:** Sonnet was used as the analyzer for all 56 Opus transcripts as planned.
- Top-level `run_summary` mirrors the latest-model stats (Opus), so single-model consumers still read correct values for the model the skill now targets.

### Run plan

- **28 evals × 2 configurations × 1 new model = 56 new Opus 4.7 runs** (primary pass).
- **No regression-run multipliers.** Unlike `pr-comments`, `peer-review/benchmark.json` has zero `run_number > 1` entries — the suite is single-run throughout. Multi-model aggregation is straightforward (no `run_number: 1` filter needed for parity, but apply it anyway for forward-compatibility).
- **Existing Sonnet 4.6 runs are not re-run.** They stay as-is (schema-upgraded in Phase 1 to gain per-run `executor_model`). Sparse time/token coverage on the Sonnet side carries over (time + tokens both have 7 of 27 paired primary runs measured, in evals 1, 3, 4, 11, 12, 13, 14) — flagged in benchmark.md, not filled in.
- **Opus runs may not have complete parent-level usage capture for time/tokens/tool_calls** (per spec 26's experience: subagent usage data was visible only in transient task-completion notifications). Record those fields as `null` where the measurement is unknown rather than inheriting Sonnet's sparse partial coverage or claiming complete Opus instrumentation; `benchmark.md` describes the Opus measurement gap explicitly instead of requiring complete Opus stats.
- **Discrimination gate does not apply.** Unlike spec 25, no evals are dropped based on Opus results. Non-discriminating evals on Opus are a finding recorded in benchmark.md, not an action item for this spec.

### Eval 26 (contamination) handling

`evals/peer-review/benchmark.json` excludes eval 26 (`unsupported-model-error`) from aggregates: the Sonnet `without_skill` run was contaminated by the executor reading `skills/peer-review/SKILL.md` from the filesystem and reproducing the skill-defined error message. Both Sonnet sides are nulled for paired-eval consistency (delta computed over 27 paired evals).

For Opus 4.7 runs:

- **Attempt the run.** Spawn the eval-26 Opus executor with the standard sandboxed workspace (`mktemp -d`, no reads outside the workspace, `without_skill` agent forbidden from reading `skills/peer-review/SKILL.md`). If the harness is properly scoped, contamination should not recur.
- **If without_skill is contaminated again** (transcript shows agent read SKILL.md or reproduced exact skill-defined phrasing it could not have inferred), null both Opus sides for paired-eval consistency, mirroring the Sonnet treatment. Document in `benchmark.md`.
- **If the run is clean,** record both Opus sides normally. The Opus paired-eval count for delta computation will be 28 (vs. Sonnet's 27); document the asymmetry in `benchmark.md` rather than nulling Opus to match.

### Interaction with existing benchmark artifacts

`evals/peer-review/` contains `benchmark.json`, `benchmark.md`, `evals.json`, and `fixtures/`. There are no committed grading-artifact JSONs for peer-review (unlike `pr-comments/`). Out of scope: any fixture changes — fixtures stay untouched.

## Files to Modify

| File | Change |
|---|---|
| `evals/peer-review/benchmark.json` | Schema upgrade to multi-model (Phase 1) → append 56 Opus 4.7 run entries (Phase 4) → recompute `run_summary` and `run_summary_by_model` |
| `evals/peer-review/benchmark.md` | Restructure Summary tables to per-model format; update Per-Eval Results table to 4-column (Sonnet with/without, Opus with/without); add "Models tested" header line with date ranges; update "Notes" / add "Known Eval Limitations" section to cover non-discriminating Opus cells and the eval 26 contamination decision |
| `README.md` | Update peer-review `Eval Δ` column to per-model format (e.g., `+26% Sonnet 4.6 / +N% Opus 4.7`); update peer-review Skill Notes `Eval cost` bullet with per-model time / token / delta stats |
| `cspell.config.yaml` | Add any new unknown words surfaced by cspell sweep |

No changes to `skills/peer-review/SKILL.md` (no skill rewrite), `evals/peer-review/evals.json` (no new evals), or `evals/peer-review/fixtures/`.

## Key Reference Files

- `evals/learn/benchmark.json` — schema template for `models_tested[]`, per-run `executor_model`, `run_summary_by_model`
- `evals/pr-comments/benchmark.json` — closest-precedent multi-model layout (Sonnet 4.6 + Opus 4.7, mid-spec analyzer fallback)
- `evals/pr-comments/benchmark.md` — prose template for per-model Summary tables and 4-column Per-Eval Results
- `specs/26-pr-comments-dual-model-benchmark/plan.md` and `tasks.md` — execution pattern (mirror phase structure exactly)
- `evals/CLAUDE.md` — benchmarking conventions (sample stddev, 2dp pass-rate delta, `null` for unrecorded stats, `eval_name` on every run, `grading.json` shape, eval 26 paired-null treatment)
- `README.md` learn / pr-comments rows — reference format for per-model `Eval Δ` column

## Branch and Worktree

- Branch: `evals/peer-review-opus-4-7-multi-model` (mirrors the learn / pr-comments naming `evals/<skill>-opus-4-7-multi-model`).
- Worktree location: `.claude/worktrees/spec-27-peer-review-dual-model`. All edits, commits, and the benchmark runs happen in the worktree; main repo is untouched until merge.
- Agents spawned with `isolation: "worktree"` must set `WT=$(git rev-parse --show-toplevel)` and prefix all Read/Edit paths with `$WT/...` (per CLAUDE.md sandbox-workarounds rule).

## Verification

1. `python3 -c 'import json; json.load(open("evals/peer-review/benchmark.json"))'` — valid JSON.
2. Every entry in `runs[]` has `executor_model` populated (one of `claude-sonnet-4-6`, `claude-opus-4-7`).
3. Every entry in `runs[]` has `eval_name` populated (preserve existing, set on new Opus entries).
4. `metadata.models_tested[]` contains exactly two blocks (Sonnet 4.6, Opus 4.7).
5. `metadata.skill_version` matches `metadata.version` in `skills/peer-review/SKILL.md` (currently `1.7`).
6. `run_summary_by_model["claude-sonnet-4-6"]` and `run_summary_by_model["claude-opus-4-7"]` both present; `stddev` uses sample formula (N−1); `delta.pass_rate` at 2 decimal places.
7. Top-level `run_summary` mirrors `run_summary_by_model["claude-opus-4-7"]` (latest-model convention).
8. `benchmark.md` Summary-table `±` values match `run_summary_by_model` exactly (spot-check via `jq`).
9. `benchmark.md` "Models tested" header names both models with date ranges.
10. `benchmark.md` Per-Eval Results table has 4 columns per eval row, and displayed pass-rate values match the corresponding `benchmark.json` runs. (Bolding indicates 100% per the table caption — not discrimination.)
11. `benchmark.md` "Notes" / "Known Eval Limitations" section documents (a) non-discriminating evals on Opus 4.7 surfaced by the run, (b) Sonnet sparse time/token coverage (7 of 27 paired primary runs measured), (c) Opus measurement gap (parent-level usage not captured), (d) the eval 26 contamination decision (clean Opus run vs. paired-null on contamination).
12. `README.md` peer-review `Eval Δ` matches per-model deltas from `run_summary_by_model[<model>].delta.pass_rate` (rounded).
13. `README.md` peer-review Skill Notes `Eval cost` bullet shows per-model time / tokens / pass-rate deltas.
14. `uv run --with pytest pytest tests/` — no regressions.
15. `npx cspell README.md evals/peer-review/benchmark.md specs/27-peer-review-dual-model-benchmark/*.md` — clean.
16. `tests/peer-review/` (if present) still passes; this spec doesn't touch the skill logic, so no new tests expected, but existing tests must not regress.

## Risks

- **Opus 4.7 runs may show 0–few discriminating cells.** The `peer-review` skill encodes a mix of universal review-mode mechanics (consistency / diff / spec mode declarations, `--focus` line, apply-prompt format) and CLI-routing mechanics (severity normalization, install hints, `## Peer Review —` header). A capable Opus baseline may derive enough of the universal mechanics to flatten several deltas, similar to `learn`'s 19-of-20 collapse. The CLI-routing evals (5–10, 15, 16, 28) are most likely to remain discriminating because they encode specific phrasing/formatting that requires reading the skill. Mitigation: frame `benchmark.md` "Known Eval Limitations" / "Notes" so the follow-up direction (purpose-refresh spec) is obvious if the pattern holds.
- **Run cost.** 56 Opus 4.7 runs — non-trivial token spend, but smaller than spec 26 (76 runs). Scope is bounded to `runs_per_configuration: 1`; no variance probing on Opus.
- **Sparse Sonnet 4.6 time/token data carries over.** The current benchmark has 7 of 27 paired primary runs with measured `time_seconds` and `tokens` (evals 1, 3, 4, 11, 12, 13, 14); the rest are `null`. Opus runs are planned to be fully instrumented but per spec 26's experience may end up with `null` time/tokens at the parent-conversation level. Mitigation: flag in `benchmark.md` prose — do not back-fill (out of scope; would require re-running the April 2026 Sonnet suite under measurement and re-instrumenting the Opus subagent harness).
- **Eval 26 contamination may recur.** If the Opus `without_skill` executor reads `skills/peer-review/SKILL.md` despite a sandboxed workspace, both Opus sides must be nulled (mirroring Sonnet) and the spec reports `+N` delta over 27 paired evals on both models. If the Opus run is clean, the Opus delta is computed over 28 paired evals and the Sonnet/Opus paired-eval counts are asymmetric (27 vs. 28); document in `benchmark.md`. Either outcome is acceptable; the spec captures the actual result, not a forced symmetry.
- **Schema upgrade of existing runs without re-running them.** Phase 1 stamps `executor_model: "claude-sonnet-4-6"` on existing entries — a purely annotative change. The benchmark data itself is untouched; only the metadata is enriched. If any existing run entry is ambiguous about its executor, audit via git blame before stamping.
- **Analyzer-model rate-limit risk (mitigated).** Spec 26 hit Opus 4.7's rate limit mid-grading and was forced to fall back to Sonnet 4.6 as the analyzer. With 56 Opus executor runs to grade (vs. spec 26's 76), the same risk exists at smaller scale. Plan: select Sonnet 4.6 as the analyzer from the start for analyzer-uniformity, avoiding the rate-limit fallback path entirely. Record `analyzer_model: "claude-sonnet-4-6"` in `metadata.models_tested[<opus>]` and the top-level `analyzer_model`. **Outcome:** Sonnet graded all 56 transcripts; no fallback was needed.

## Shipping

1. Work happens on branch `evals/peer-review-opus-4-7-multi-model` in worktree `.claude/worktrees/spec-27-peer-review-dual-model`.
2. Execute Phases 1–7 in the worktree.
3. Stage all changes; open PR from the branch.
4. Run `/pr-comments {pr_number}` immediately after PR creation (per CLAUDE.md post-push convention).
5. Loop `/pr-comments` until no new bot feedback.
6. Run `/pr-human-guide` to annotate for human reviewers.
7. Squash-merge after human approval; delete branch; sync local main; clean up worktree directory.
