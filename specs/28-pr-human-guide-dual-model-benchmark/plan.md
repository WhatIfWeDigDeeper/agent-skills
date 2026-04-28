# Spec 28: pr-human-guide — dual-model benchmarking (Sonnet 4.6 + Opus 4.7)

## Context

Prior to spec 28, the `pr-human-guide` skill is benchmarked only on `claude-sonnet-4-6` and at SKILL.md `v0.1` (see `evals/pr-human-guide/benchmark.json` — top-level `metadata.executor_model: "claude-sonnet-4-6"`, `metadata.skill_version: "0.1"`, 8 evals × 2 configs × 1 run each = 16 runs, all `run_number == 1`, with-vs-without delta `+0.39` [+39 pp]). The skill itself has since advanced to `v0.7` through six commits — including a behavioral change in PR #112 that switches review-guide items to checkboxes — so the existing baseline conflates model effect with skill-version effect. Specs 25 (`learn`), 26 (`pr-comments`), and 27 (`peer-review`) established the canonical multi-model schema: `metadata.models_tested[]`, per-run `executor_model`, `run_summary_by_model`, and a per-model prose structure in `benchmark.md`.

Adding Opus 4.7 to `pr-human-guide` serves two purposes:

1. **Publish per-model deltas** so the README's `Eval Δ` column and the skill-notes `Eval cost` bullet reflect both production models, matching the reporting standard `learn`, `pr-comments`, and `peer-review` now set.
2. **Surface non-discriminating evals on Opus 4.7.** When `learn` was benchmarked on Opus 4.7, 19 of 20 cells stopped discriminating — the base model had internalized the skill's behaviors. `pr-comments` showed a softer pattern (delta dropped from +63 to +39 pp; 9 non-discriminating Opus cells). `peer-review` showed a +34 pp Opus delta with 8 non-discriminating cells. The current Sonnet baseline already has 2 of 8 non-discriminating cells (evals 7 `data-model-changes`, 8 `concurrency-state` — both 4/4 in both configurations); Opus is likely to flatten more. This spec reports the signal; it does **not** rewrite the skill or add new evals.

**Skill-version baseline reset.** Unlike specs 26 and 27 (which preserved their existing Sonnet runs because Sonnet was at the same SKILL.md version as the new Opus pass), spec 28 must re-run Sonnet 4.6 at `v0.7` so both models share an apples-to-apples skill version. The existing `v0.1` Sonnet runs are removed from `runs[]` entirely (not preserved as historical) — `git history` retains the prior benchmark.json shape if needed. Phase 1 deletes them and resets the schema to the multi-model shape; the v0.7 Sonnet runs are *generated* in Phases 2–3, the Opus runs in Phases 4–5, and all 32 entries are *appended to `runs[]`* in Phase 6 alongside grading.

**Scope deliberately narrower than spec 25.** Spec 25 bundled dual-model benchmarking with a skill rewrite and four new evals. Specs 26, 27, and 28 are dual-model benchmarking only. Skill rewrites and new evals — if warranted by Opus 4.7 results — are a follow-up spec.

## Design

### Schema changes (from `evals/learn/benchmark.json`, `evals/pr-comments/benchmark.json`, `evals/peer-review/benchmark.json`)

Mirror the multi-model schema established in specs 25, 26, and 27:

- `metadata.models_tested[]`: array with one block per model. Each block carries that model's `executor_model`, `analyzer_model`, `timestamp`, `runs_per_configuration`, and `notes`.
- Per-run `executor_model` field on every entry in `runs[]` — Sonnet runs get `"claude-sonnet-4-6"`; Opus runs get `"claude-opus-4-7"`.
- `run_summary_by_model` keyed by model name, each containing `pass_rate`, `time_seconds`, `tokens` with `mean`/`stddev`/`min`/`max`, plus a `delta` section comparing `with_skill` vs `without_skill` for that model.
- Top-level `metadata.executor_model` flips to the latest model (`claude-opus-4-7`) — latest-model convention from `learn`, `pr-comments`, `peer-review`. Top-level `analyzer_model` reflects the actual analyzer used by the latest-model row; following spec 27's mitigation, **select Sonnet 4.6 as the analyzer from the start** for analyzer-uniformity (records `analyzer_model: "claude-sonnet-4-6"` on the Opus row).
- Top-level `run_summary` mirrors the latest-model stats (Opus), so single-model consumers still read correct values for the model the skill now targets.
- `metadata.skill_version` set explicitly to the current SKILL.md version (`"0.7"`) for both model blocks and at the top level.

### Run plan

- **8 evals × 2 configurations × 2 models = 32 new runs** at SKILL.md `v0.7`.
- **No regression-run multipliers.** All entries are `run_number == 1` (matching the existing single-run shape and spec 27's pattern; smallest run set in the dual-model series so far).
- **Existing v0.1 Sonnet runs are removed.** Phase 1 deletes them from `runs[]` and resets the schema to the multi-model shape; Sonnet runs are generated in Phases 2–3, Opus runs in Phases 4–5, and all 32 entries are appended to `runs[]` in Phase 6 after grading. Git history preserves the prior file shape; no historical archive is kept inside `benchmark.json`.
- **Opus runs may not have complete parent-level usage capture for time/tokens/tool_calls** (per spec 26's experience: subagent usage data was visible only in transient task-completion notifications). Record those fields as `null` where the measurement is unknown rather than fabricating values. The Sonnet runs at `v0.7` are planned to be fully instrumented but the same parent-level capture caveat applies; record `null` rather than partial data when measurement is unknown.
- **Discrimination gate does not apply.** Unlike spec 25, no evals are dropped based on Opus results. Non-discriminating evals on Opus are a finding recorded in benchmark.md, not an action item for this spec.

### Analyzer-model choice

Mirror spec 27: **Sonnet 4.6 is the sole grader for all 32 transcripts**, including the 16 Opus transcripts. Selected from the start (vs spec 26's mid-grading Opus → Sonnet fallback) for analyzer-uniformity — no Opus self-grading, no fallback to a different analyzer mid-grading. With only 32 transcripts to grade — well below spec 27's 56 and spec 26's 76 — rate-limit risk is low. Record `analyzer_model: "claude-sonnet-4-6"` on every entry in `runs[]`, in both model blocks of `metadata.models_tested[]`, and at the top level.

### Interaction with existing benchmark artifacts

`evals/pr-human-guide/` contains `benchmark.json`, `benchmark.md`, `evals.json`, and `workspace/`. The skill's category taxonomy lives in `skills/pr-human-guide/references/categories.md` (not under `evals/`). There are no committed grading-artifact JSONs for `pr-human-guide` (like `peer-review`, unlike `pr-comments`). Out of scope: any `evals.json` changes (no new evals), any `skills/pr-human-guide/references/categories.md` changes (the skill itself stays untouched), any `workspace/` changes.

## Files to Modify

| File | Change |
|---|---|
| `evals/pr-human-guide/benchmark.json` | Schema reset to multi-model shape; remove existing v0.1 Sonnet runs (Phase 1) → generate Sonnet 4.6 v0.7 transcripts (Phases 2–3) → generate Opus 4.7 transcripts (Phases 4–5) → grade all 32 transcripts and append entries to `runs[]`, populate `models_tested[]`, flip top-level metadata, recompute `run_summary` and `run_summary_by_model` (Phase 6) |
| `evals/pr-human-guide/benchmark.md` | Restructure Summary tables to per-model format; update Per-Eval Results table to 4-column (Sonnet with/without, Opus with/without); add "Models tested" header line with date ranges; add "Known Eval Limitations" section to cover non-discriminating Opus cells, the v0.1 → v0.7 skill-version reset rationale, and any Opus measurement gap |
| `README.md` | Update pr-human-guide `Eval Δ` column to per-model format (e.g., `+39% Sonnet 4.6 / +N% Opus 4.7`); update pr-human-guide Skill Notes `Eval cost` bullet with per-model time / token / pass-rate stats |
| `cspell.config.yaml` | Add any new unknown words surfaced by cspell sweep (alphabetically sorted) |

No changes to `skills/pr-human-guide/SKILL.md` (no skill rewrite), `skills/pr-human-guide/references/categories.md` (taxonomy stays as-is), `evals/pr-human-guide/evals.json` (no new evals), or `evals/pr-human-guide/workspace/`.

## Key Reference Files

- `evals/learn/benchmark.json` — schema template for `models_tested[]`, per-run `executor_model`, `run_summary_by_model`
- `evals/pr-comments/benchmark.json` — closest-precedent multi-model layout with regression-run multipliers
- `evals/peer-review/benchmark.json` — closest-precedent multi-model layout without regression-run multipliers (run-count parity with spec 28's plan)
- `evals/pr-comments/benchmark.md` and `evals/peer-review/benchmark.md` — prose templates for per-model Summary tables and 4-column Per-Eval Results
- `specs/26-pr-comments-dual-model-benchmark/` and `specs/27-peer-review-dual-model-benchmark/` — execution pattern (mirror phase structure)
- `evals/CLAUDE.md` — benchmarking conventions (sample stddev, 2dp pass-rate delta, `null` for unrecorded stats, `eval_name` on every run, `grading.json` shape, subagent-based eval execution rules)
- `README.md` learn / pr-comments / peer-review rows — reference format for per-model `Eval Δ` column

## Branch and Worktree

- Branch: `evals/pr-human-guide-opus-4-7-multi-model` (mirrors the learn / pr-comments / peer-review naming `evals/<skill>-opus-4-7-multi-model`).
- Worktree location: `.claude/worktrees/spec-28-pr-human-guide-dual-model`. All edits, commits, and the benchmark runs happen in the worktree; main repo is untouched until merge.
- Agents spawned with `isolation: "worktree"` must set `WT=$(git rev-parse --show-toplevel)` and prefix all Read/Edit paths with `$WT/...` (per CLAUDE.md sandbox-workarounds rule).

## Verification

1. `python3 -c 'import json; json.load(open("evals/pr-human-guide/benchmark.json"))'` — valid JSON.
2. Every entry in `runs[]` has `executor_model` populated (one of `claude-sonnet-4-6`, `claude-opus-4-7`).
3. Every entry in `runs[]` has `eval_name` populated.
4. `runs[]` length is exactly 32 (8 evals × 2 configs × 2 models, no v0.1 entries remain).
5. `metadata.models_tested[]` contains exactly two blocks (Sonnet 4.6 v0.7, Opus 4.7 v0.7).
6. `metadata.skill_version` matches `metadata.version` in `skills/pr-human-guide/SKILL.md` (currently `0.7`).
7. `run_summary_by_model["claude-sonnet-4-6"]` and `run_summary_by_model["claude-opus-4-7"]` both present; `stddev` uses sample formula (N−1); `delta.pass_rate` at 2 decimal places.
8. Top-level `run_summary` is deep-equal to `run_summary_by_model["claude-opus-4-7"]` — full block (`with_skill`, `without_skill`, `delta`), not just the headline mean (latest-model convention; matches the precedent in `evals/peer-review/benchmark.json` and `evals/pr-comments/benchmark.json`).
9. `benchmark.md` Summary-table `±` values match `run_summary_by_model` exactly — for each model, configuration, and metric, the rendered `mean ±stddev` corresponds to `jq -r '.run_summary_by_model["<model>"].<config>.<metric> | "\(.mean) ±\(.stddev)"' evals/pr-human-guide/benchmark.json` (modulo display formatting, e.g. `1.0 ±0.0` rendered as `100% ±0%`).
10. `benchmark.md` "Models tested" header names both models with date ranges.
11. `benchmark.md` Per-Eval Results table has 4 columns per eval row, and displayed pass-rate values match the corresponding `benchmark.json` runs.
12. `benchmark.md` "Known Eval Limitations" section documents (a) non-discriminating evals on each model with eval ids (Sonnet baseline already has evals 7 and 8 non-discriminating), (b) the skill-version reset rationale (v0.1 → v0.7), (c) Opus measurement gap if parent-level usage was not captured.
13. `README.md` pr-human-guide `Eval Δ` matches per-model deltas from `run_summary_by_model[<model>].delta.pass_rate` (rounded).
14. `README.md` pr-human-guide Skill Notes `Eval cost` bullet shows per-model time / tokens / pass-rate deltas.
15. `uv run --with pytest pytest tests/` — no regressions.
16. `npx cspell README.md evals/pr-human-guide/benchmark.md specs/28-pr-human-guide-dual-model-benchmark/*.md` — clean.

## Risks

- **Opus 4.7 may show 0–few discriminating cells.** The `pr-human-guide` skill encodes (a) a fixed six-category taxonomy, (b) SHA-256 GitHub diff anchor format, and (c) idempotent `<!-- pr-human-guide --> ... <!-- /pr-human-guide -->` HTML markers. Capable Opus baseline may derive enough of the categorization to flatten several deltas, similar to `learn`'s 19-of-20 collapse. Anchor format and HTML-marker idempotency evals are most likely to remain discriminating because they encode specific phrasing/formatting that requires reading the skill. Mitigation: frame `benchmark.md` "Known Eval Limitations" so the follow-up direction (purpose-refresh spec) is obvious if the pattern holds.
- **Run cost.** 32 runs total (16 Sonnet + 16 Opus) — smaller than spec 26 (76) and spec 27 (56). Scope is bounded to `runs_per_configuration: 1`; no variance probing.
- **Sonnet baseline drift on re-run.** The current `+39%` Sonnet baseline at v0.1 may shift up or down at v0.7 — the checkbox change (PR #112) and other behavioral commits could move pass rates either direction. The spec captures whatever the v0.7 Sonnet result actually is; a notable shift is documented in `benchmark.md` as a finding (not as a problem).
- **Opus measurement gap.** Per spec 26's experience, parent-level usage data (time/tokens/tool_calls) for subagent-spawned executors may only be visible in transient task-completion notifications and not preserved at the parent level. Mitigation: record `null` for unknown stats; describe the measurement gap in `benchmark.md` rather than fabricating partial coverage.
- **Schema-reset risk.** Phase 1 deletes the existing v0.1 Sonnet `runs[]` entries — git history is the only remaining source for the prior shape. Mitigation: Phase 1 is its own commit so the deletion is clearly separated from the Phase 2+ append work; reviewers can diff against the prior commit if comparison to v0.1 is later needed.
- **Analyzer-model rate-limit risk (mitigated).** Spec 26 hit Opus 4.7's rate limit mid-grading at 76 transcripts and was forced to fall back to Sonnet. With 32 transcripts to grade, the same risk exists at much smaller scale. Plan: select Sonnet 4.6 as the analyzer from the start for analyzer-uniformity, avoiding the rate-limit fallback path entirely. Record `analyzer_model: "claude-sonnet-4-6"` in `metadata.models_tested[<both>]` and at the top level.

## Shipping

1. In Phase 0, create branch `evals/pr-human-guide-opus-4-7-multi-model` and a worktree at `.claude/worktrees/spec-28-pr-human-guide-dual-model` checked out to that branch (via `git worktree add .claude/worktrees/spec-28-pr-human-guide-dual-model -b evals/pr-human-guide-opus-4-7-multi-model`). All Phase 0 work — including the pre-spec peer review and the post-review spec-doc commit — runs in the worktree, not the main repo.
2. Execute Phase 0 (pre-spec peer review of plan.md/tasks.md via `copilot:gpt-5.4`, iteration cap 2, auto-approve valid) before any benchmark runs. The post-review spec-doc commit is the first commit on the branch. Phase 0 caps at 2 iterations because the surface area is two short Markdown files and a third pass is unlikely to surface anything beyond cosmetic churn; Phase 9 caps higher (4) because it covers the full multi-file implementation where cross-file drift compounds.
3. Execute Phases 1–9 in the worktree (final benchmark.json/benchmark.md/README.md edits, verification, and post-implementation peer review).
4. Execute Phase 10 (Ship): stage all changes; open PR from the branch.
5. Run `/pr-comments {pr_number}` immediately after PR creation (per CLAUDE.md post-push convention).
6. Loop `/pr-comments` until no new bot feedback.
7. Run `/pr-human-guide` to annotate for human reviewers (dogfood the skill being benchmarked).
8. Squash-merge after human approval; delete branch; sync local main; clean up worktree directory.
