# Spec 29: ship-it — dual-model benchmarking (Sonnet 4.6 + Opus 4.7)

## Context

Prior to spec 29, the `ship-it` skill is benchmarked only on `claude-sonnet-4-6`, with no recorded `metadata.skill_version` (see `evals/ship-it/benchmark.json` — top-level `metadata.executor_model: "claude-sonnet-4-6"`, `timestamp: "2026-03-11T15:30:00Z"`, 3 evals × 2 configurations × 1 run each = 6 runs in `runs[]`, all `run_number == 1`, with-vs-without delta `+0.38` [+38 pp]). The skill itself has since advanced through six commits to `version: "0.5"` (latest: `cdbde22 trim(ship-it): minimum viable rule text (#121)`), so the existing baseline conflates model effect with skill-version effect. Specs 25 (`learn`), 26 (`pr-comments`), 27 (`peer-review`), and 28 (`pr-human-guide`) established the canonical multi-model schema: `metadata.models_tested[]`, per-run `executor_model`, `run_summary_by_model`, and a per-model prose structure in `benchmark.md`. `ship-it` is the remaining production-tier skill in `README.md`'s Available Skills table that still reports a single-model `Eval Δ`.

Two pre-existing data-integrity issues surface and must be fixed in the same pass:

1. **eval_id mislabel.** The third entry pair in `runs[]` carries `eval_id: 3` but `eval_name: "refactor-with-branch-name"`, which is `evals.json` id `4`. `evals.json` id `3` is `branch-name-collision`. The benchmark.json predates the addition of `branch-name-collision` to `evals.json`; when that eval was inserted at id 3, the older `refactor-with-branch-name` run kept its `eval_id: 3` and was not renumbered to `4`. The Phase 1 schema reset clears `runs[]`, so the re-run lands with correct ids.
2. **`branch-name-collision` (id 3) has never been run.** Its fixture requires a git remote with the natural branch name (`docs/update-readme`) pre-existing — meaningfully more setup than the other three evals (which just need an empty git workspace + scripted `gh` interactions). This spec leaves it un-run for the same reason prior benchmark passes did, and documents the gap explicitly in `benchmark.md` "Known Eval Limitations". Filling it is a candidate follow-up spec, not in scope here.

Adding Opus 4.7 to `ship-it` serves two purposes:

1. **Publish per-model deltas** so the README's `Eval Δ` column and the skill-notes `Eval cost` bullet reflect both production models, matching the reporting standard `learn`, `pr-comments`, `peer-review`, and `pr-human-guide` now set.
2. **Surface non-discriminating evals on Opus 4.7.** When `learn` was benchmarked on Opus 4.7, 19 of 20 cells stopped discriminating — the base model had internalized the skill's behaviors. `pr-comments` showed a softer pattern (delta dropped from +63 to +39 pp; 9 non-discriminating Opus cells). `peer-review` showed a +34 pp Opus delta with 8 non-discriminating cells. `pr-human-guide` (spec 28) showed +42 pp Opus delta with its own pattern. `ship-it`'s three runnable evals all currently differentiate at 1.00/0.625 on Sonnet — the three `with_skill` exclusives are `runs-divergence-check` (`git fetch`), `runs-ls-remote-branch-check` (collision check), and `gh-pr-create-uses-base-flag` (`--base` flag). Opus 4.7 may have internalized one or more of these process steps. This spec reports the signal; it does **not** rewrite the skill or add new evals.

**Skill-version baseline reset.** Like spec 28 (and unlike specs 26/27, which preserved their existing Sonnet runs because Sonnet was at the same SKILL.md version as the new Opus pass), spec 29 must re-run Sonnet 4.6 at `v0.5` so both models share an apples-to-apples skill version. The existing version-unspecified Sonnet runs are removed from `runs[]` entirely (not preserved as historical) — `git history` retains the prior `benchmark.json` shape if needed. Phase 1 deletes them and resets the schema to the multi-model shape; the v0.5 Sonnet runs are *generated* in Phases 2–3, the Opus runs in Phases 4–5, and all 12 entries are *appended to `runs[]`* in Phase 6 alongside grading.

**Scope deliberately narrower than spec 25.** Spec 25 bundled dual-model benchmarking with a skill rewrite and four new evals. Specs 26, 27, 28, and 29 are dual-model benchmarking only. Skill rewrites, new evals, and the `branch-name-collision` fixture build-out — if warranted by Opus 4.7 results — are follow-up specs.

## Design

### Schema changes (mirror `evals/learn/benchmark.json`, `evals/pr-comments/benchmark.json`, `evals/peer-review/benchmark.json`, `evals/pr-human-guide/benchmark.json`)

Mirror the multi-model schema established in specs 25, 26, 27, and 28:

- `metadata.models_tested[]`: array with one block per model. Each block carries that model's `executor_model`, `analyzer_model`, `timestamp`, `runs_per_configuration`, `skill_version: "0.5"`, and `notes`.
- Per-run `executor_model` field on every entry in `runs[]` — Sonnet runs get `"claude-sonnet-4-6"`; Opus runs get `"claude-opus-4-7"`.
- Per-run `analyzer_model: "claude-sonnet-4-6"` on every entry without exception (analyzer-uniformity, mirrored from spec 27/28).
- `run_summary_by_model` keyed by model name, each containing `pass_rate`, `time_seconds`, `tokens`, `cache_tokens` with `mean`/`stddev`/`min`/`max`, plus a `delta` section comparing `with_skill` vs `without_skill` (covering all four metrics, including `cache_tokens` as a separate signed-string delta — `tokens` is `input_tokens + output_tokens` while `cache_tokens` is `cache_creation_input_tokens + cache_read_input_tokens`, kept distinct because cache reads bill at 0.1× and creation at 1.25–2×).
- Top-level `metadata.executor_model` flips to the latest model (`claude-opus-4-7`) — latest-model convention from `learn`, `pr-comments`, `peer-review`, `pr-human-guide`. Top-level `analyzer_model` reflects the actual analyzer used by the latest-model row; following spec 27/28's mitigation, **select Sonnet 4.6 as the analyzer from the start** for analyzer-uniformity (records `analyzer_model: "claude-sonnet-4-6"` on the Opus row).
- Top-level `run_summary` mirrors the latest-model stats (Opus), so single-model consumers still read correct values for the model the skill now targets.
- `metadata.skill_version` set explicitly to the current SKILL.md version (`"0.5"`) for both model blocks and at the top level. This **backfills the missing field** that the prior `ship-it` benchmark left undeclared.
- `metadata.evals_run` set to `[1, 2, 4]` — corrects the prior `[1, 2, 3]` that mislabeled `refactor-with-branch-name` as eval 3.

### Run plan

- **3 evals × 2 configurations × 2 models = 12 new runs** at SKILL.md `v0.5`.
- **No regression-run multipliers.** All entries are `run_number == 1` (matching the existing single-run shape and specs 27/28's pattern; smallest run set in the dual-model series so far).
- **eval_id correction.** The existing 3rd-pair entries (mislabeled `eval_id: 3` for `refactor-with-branch-name`) are removed in Phase 1 and re-generated in Phases 2–5 with `eval_id: 4` and `eval_name: "refactor-with-branch-name"` (matching `evals.json`).
- **Eval 3 (`branch-name-collision`) is NOT run.** Its fixture requires a git remote with `docs/update-readme` pre-existing — meaningfully heavier setup than the other three evals (writable workspace, real git remote with that branch). Documented in Phase 7's "Known Eval Limitations" as a follow-up candidate.
- **Existing Sonnet runs are removed.** Phase 1 deletes them from `runs[]` and resets the schema to the multi-model shape; Sonnet runs are generated in Phases 2–3, Opus runs in Phases 4–5, and all 12 entries are appended to `runs[]` in Phase 6 after grading. Git history preserves the prior file shape; no historical archive is kept inside `benchmark.json`.
- **Opus runs may not have complete parent-level usage capture for time/tokens/tool_calls** (per specs 26/27/28's experience: subagent usage data was visible only in transient task-completion notifications). Record those fields as `null` where the measurement is unknown rather than fabricating values. The Sonnet runs at `v0.5` are planned to be fully instrumented but the same parent-level capture caveat applies; record `null` rather than partial data when measurement is unknown.
- **Null-handling for aggregates.** When computing `run_summary_by_model[<model>].<config>.<metric>` (mean / stddev / min / max), exclude `null` values from the sample. If a (model, configuration, metric) cell has no non-null values, set every field of that summary block to `null` and use `null` as the input to the corresponding `delta` computation; the delta string itself becomes `null` rather than a signed string. `pass_rate` is always non-null (grading produces a value), so `pass_rate` summaries never collapse to null in practice. `benchmark.md` renders any null summary value as `N/A` (matches `evals/peer-review/benchmark.md`'s convention for the time/token rows).
- **Discrimination gate does not apply.** Unlike spec 25, no evals are dropped based on Opus results. Non-discriminating evals on Opus are a finding recorded in `benchmark.md`, not an action item for this spec.

### Analyzer-model choice

Mirror specs 27/28: **Sonnet 4.6 is the sole grader for all 12 transcripts**, including the 6 Opus transcripts. Selected from the start (vs spec 26's mid-grading Opus → Sonnet fallback) for analyzer-uniformity — no Opus self-grading, no fallback to a different analyzer mid-grading. With only 12 transcripts to grade — the smallest run set in the dual-model series so far (well below specs 26's 76, 27's 56, 28's 32) — rate-limit risk is negligible. Record `analyzer_model: "claude-sonnet-4-6"` on every entry in `runs[]`, in both model blocks of `metadata.models_tested[]`, and at the top level.

### Interaction with existing benchmark artifacts

`evals/ship-it/` contains `benchmark.json`, `benchmark.md`, `evals.json`, and `trigger_eval.json`. There are no committed grading-artifact JSONs (matching `peer-review` and `pr-human-guide`; unlike `pr-comments`). No `workspace/` directory. Out of scope: any `evals.json` changes (no new evals, no fixture build-out for eval 3), `trigger_eval.json` changes, `skills/ship-it/SKILL.md` rewrites, fixture additions for eval 3.

## Files to Modify

| File | Change |
|---|---|
| `evals/ship-it/benchmark.json` | Schema reset to multi-model shape; remove existing Sonnet runs (Phase 1) → generate Sonnet 4.6 v0.5 transcripts (Phases 2–3) → generate Opus 4.7 transcripts (Phases 4–5) → grade all 12 transcripts and append entries to `runs[]`, populate `models_tested[]`, flip top-level metadata, recompute `run_summary` and `run_summary_by_model` (Phase 6). Backfill missing `metadata.skill_version`. Fix the prior eval_id mislabel (was eval_id 3 with `eval_name: "refactor-with-branch-name"`; should be eval_id 4). Set `metadata.evals_run` to `[1, 2, 4]`. |
| `evals/ship-it/benchmark.md` | Restructure Summary tables to per-model format; update Per-Eval Results table to 4-column (Sonnet with/without, Opus with/without); add "Models tested" header line with date ranges; add "Known Eval Limitations" section to cover non-discriminating Opus cells, the prior version-unspecified → v0.5 skill-version reset rationale and the eval_id-3 mislabel correction, the eval 3 (`branch-name-collision`) gap with fixture-cost rationale, and any Opus measurement gap. |
| `README.md` | Update ship-it `Eval Δ` column to per-model format (e.g., `+38% Sonnet 4.6 / +N% Opus 4.7`); update ship-it Skill Notes `Eval cost` bullet with per-model time / tokens / pass-rate stats — replacing the current `+41.0 seconds, +5,073 tokens over baseline` framing. |
| `cspell.config.yaml` | Add any new unknown words surfaced by cspell sweep (alphabetically sorted). |

No changes to `skills/ship-it/SKILL.md` (no skill rewrite), `skills/ship-it/references/` (untouched), `evals/ship-it/evals.json` (no new evals, no fixture build-out for eval 3), or `evals/ship-it/trigger_eval.json`.

## Key Reference Files

- `specs/28-pr-human-guide-dual-model-benchmark/{plan,tasks}.md` — closest precedent; mirror phase structure exactly.
- `evals/pr-human-guide/benchmark.json` — closest-precedent multi-model layout (run-count parity: 32 runs there vs 12 here, both at `runs_per_configuration: 1`).
- `evals/peer-review/benchmark.json` and `evals/pr-comments/benchmark.json` — additional multi-model layout examples.
- `evals/peer-review/benchmark.md` and `evals/pr-human-guide/benchmark.md` — prose templates for per-model Summary tables and 4-column Per-Eval Results.
- `evals/CLAUDE.md` — benchmarking conventions (sample stddev, 2dp pass-rate delta, `null` for unrecorded stats, `eval_name` on every run, `grading.json` shape, `tokens` vs `cache_tokens` split, subagent-based eval execution rules including the executor-must-not-call-`Skill`-tool rule).
- `README.md` learn / pr-comments / peer-review / pr-human-guide rows — reference format for per-model `Eval Δ` column and `Eval cost` bullet.

## Branch and Worktree

- Branch: `evals/ship-it-opus-4-7-multi-model` (mirrors the learn / pr-comments / peer-review / pr-human-guide naming `evals/<skill>-opus-4-7-multi-model`).
- Worktree location: `.claude/worktrees/spec-29-ship-it-dual-model`. All edits, commits, and the benchmark runs happen in the worktree; main repo is untouched until merge.
- Agents spawned with `isolation: "worktree"` must set `WT=$(git rev-parse --show-toplevel)` and prefix all Read/Edit paths with `$WT/...` (per CLAUDE.md sandbox-workarounds rule).

## Verification

1. `python3 -c 'import json; json.load(open("evals/ship-it/benchmark.json"))'` — valid JSON.
2. Every entry in `runs[]` has `executor_model` populated (one of `claude-sonnet-4-6`, `claude-opus-4-7`).
3. Every entry in `runs[]` has `eval_name` populated.
4. `runs[]` length is exactly 12 (3 evals × 2 configs × 2 models, no version-unspecified entries remain).
5. `metadata.models_tested[]` contains exactly two blocks (Sonnet 4.6 v0.5, Opus 4.7 v0.5).
6. `metadata.skill_version` matches the `version` value in `skills/ship-it/SKILL.md` (currently `"0.5"`).
7. `metadata.evals_run` is `[1, 2, 4]` — matches the actually-run set after eval_id correction.
8. Every `runs[]` entry's `eval_id` matches its `eval_name` against `evals.json` (no entry has `eval_id: 3` paired with `eval_name: "refactor-with-branch-name"`).
9. `run_summary_by_model["claude-sonnet-4-6"]` and `run_summary_by_model["claude-opus-4-7"]` both present; `stddev` uses sample formula (N−1); `delta.pass_rate` at 2 decimal places; `delta.time_seconds` / `delta.tokens` / `delta.cache_tokens` are signed strings.
10. Top-level `run_summary` is deep-equal to `run_summary_by_model["claude-opus-4-7"]` — full block (`with_skill`, `without_skill`, `delta`), not just the headline mean (latest-model convention; matches the precedent in `evals/peer-review/benchmark.json`, `evals/pr-comments/benchmark.json`, and `evals/pr-human-guide/benchmark.json`).
11. `benchmark.md` Summary-table `±` values match `run_summary_by_model` exactly — for each model, configuration, and metric, the rendered `mean ±stddev` corresponds to `jq -r '.run_summary_by_model["<model>"].<config>.<metric> | "\(.mean) ±\(.stddev)"' evals/ship-it/benchmark.json` (modulo display formatting, e.g. `1.0 ±0.0` rendered as `100% ±0%`).
12. `benchmark.md` "Models tested" header names both models with date ranges.
13. `benchmark.md` Per-Eval Results table has 4 columns per eval row, and displayed pass-rate values match the corresponding `benchmark.json` runs.
14. `benchmark.md` "Known Eval Limitations" section documents (a) for each model, every eval id where both `with_skill` and `without_skill` pass rates are 1.0; (b) the prior version-unspecified → v0.5 skill-version reset rationale, plus the eval_id-3 mislabel correction; (c) eval 3 (`branch-name-collision`) gap with fixture-cost rationale; (d) any Opus parent-level measurement gap encountered (or note explicitly if measurements were captured cleanly).
15. `README.md` ship-it `Eval Δ` matches per-model deltas from `run_summary_by_model[<model>].delta.pass_rate` (rounded).
16. `README.md` ship-it Skill Notes `Eval cost` bullet shows per-model time / tokens / pass-rate deltas (no longer the single-model `+41.0 seconds, +5,073 tokens over baseline` framing).
17. `uv run --with pytest pytest tests/` — no regressions.
18. `npx cspell README.md evals/ship-it/benchmark.md specs/29-ship-it-dual-model-benchmark/*.md` — clean.

## Risks

- **Opus 4.7 may show 0–few discriminating cells.** ship-it's three discriminating assertions are all process-checks the skill reminds the agent to perform: `git fetch` divergence check, `git ls-remote --heads origin` branch-name check, and `--base` on `gh pr create`. A capable Opus baseline may have internalized one or more of these. The two `git`-related ones are the most likely to flatten (they are well-known good practice); `--base` is more specific to fork-PR safety and may stay discriminating. Mitigation: frame `benchmark.md` "Known Eval Limitations" so the follow-up direction (purpose-refresh spec) is obvious if multiple cells flatten.
- **Run cost.** 12 runs total (6 Sonnet + 6 Opus) — the smallest run set in the dual-model series so far. ship-it runs are also the most expensive in real-time terms (each run does branch creation + commit + push + `gh pr create` against a sandboxed git/gh fixture, ~115s with-skill on Sonnet historically); plan for ~25 minutes of executor wall-clock in total assuming similar fixture costs at v0.5.
- **Sonnet baseline drift on re-run.** The current `+38%` Sonnet baseline was captured at an unspecified earlier version. The re-run may shift up or down at v0.5; the spec captures whatever the v0.5 Sonnet result actually is. A notable shift is documented in `benchmark.md` as a finding (not as a problem).
- **Opus measurement gap.** Per specs 26/27/28's experience, parent-level usage data (time/tokens/tool_calls) for subagent-spawned executors may only be visible in transient task-completion notifications and not preserved at the parent level. Mitigation: record `null` for unknown stats; describe the measurement gap in `benchmark.md` rather than fabricating partial coverage.
- **Schema-reset risk.** Phase 1 deletes the existing Sonnet `runs[]` entries — git history is the only remaining source for the prior shape. Mitigation: Phase 1 is its own commit so the deletion is clearly separated from the Phase 2+ append work; reviewers can diff against the prior commit if comparison to the pre-spec state is later needed.
- **Eval 3 fixture cost.** Skipping `branch-name-collision` means the spec doesn't surface whether Opus 4.7 changes that eval's discrimination. Mitigation: explicit "Known Eval Limitations" entry plus a follow-up-candidate flag — keeps scope honest and points at the next spec.
- **Analyzer-model rate-limit risk (mitigated).** Spec 26 hit Opus 4.7's rate limit mid-grading at 76 transcripts and was forced to fall back to Sonnet. With 12 transcripts to grade, the same risk exists at much smaller scale. Plan: select Sonnet 4.6 as the analyzer from the start for analyzer-uniformity, avoiding the rate-limit fallback path entirely. Record `analyzer_model: "claude-sonnet-4-6"` in `metadata.models_tested[<both>]` and at the top level.
- **Skill-version backfill ambiguity.** The prior benchmark.json had no `metadata.skill_version` field. The Phase 1 reset adds it as `"0.5"` (current SKILL.md version). Document in `benchmark.md` that the prior runs are removed (not retained as a different-version row) precisely because their skill version is unknown — re-running at v0.5 is the cleanest baseline.

## Shipping

1. In Phase 0, create branch `evals/ship-it-opus-4-7-multi-model` and a worktree at `.claude/worktrees/spec-29-ship-it-dual-model` checked out to that branch (via `git worktree add .claude/worktrees/spec-29-ship-it-dual-model -b evals/ship-it-opus-4-7-multi-model`). All Phase 0 work — including the pre-spec peer review and the post-review spec-doc commit — runs in the worktree, not the main repo.
2. Execute Phase 0 (pre-spec peer review of plan.md/tasks.md via `copilot:gpt-5.4`, iteration cap 2, auto-approve valid) before any benchmark runs. The post-review spec-doc commit is the first commit on the branch. Phase 0 caps at 2 iterations because the surface area is two short Markdown files and a third pass is unlikely to surface anything beyond cosmetic churn; Phase 9 caps higher (4) because it covers the full multi-file implementation where cross-file drift compounds.
3. Execute Phases 1–9 in the worktree (final benchmark.json/benchmark.md/README.md edits, verification, and post-implementation peer review).
4. Execute Phase 10 (Ship): stage all changes; open PR from the branch.
5. Run `/pr-comments {pr_number}` immediately after PR creation (per CLAUDE.md post-push convention).
6. Loop `/pr-comments` until no new bot feedback.
7. Run `/pr-human-guide` to annotate for human reviewers.
8. Squash-merge after human approval; delete branch; sync local main; clean up worktree directory.
