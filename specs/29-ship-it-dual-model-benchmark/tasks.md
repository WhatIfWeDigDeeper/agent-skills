# Spec 29: Tasks — ship-it dual-model benchmarking

## Phase 0: Pre-spec peer review (consistency pass on plan.md and tasks.md)

*Catch drift between `plan.md` and `tasks.md` before any benchmark runs commit. Uses an external CLI reviewer for fresh-context judgment on the spec docs themselves. Auto-approves valid findings; iteration cap 2.*

- [x] **0.1** Create branch `evals/ship-it-opus-4-7-multi-model` and a worktree at `.claude/worktrees/spec-29-ship-it-dual-model` checked out to that branch in one step: `git worktree add .claude/worktrees/spec-29-ship-it-dual-model -b evals/ship-it-opus-4-7-multi-model`. All subsequent Phase 0–9 work runs inside the worktree, not the main repo. Stage `specs/29-ship-it-dual-model-benchmark/plan.md` and `tasks.md` (already present in the worktree via the branch checkout).
- [x] **0.2** Run `/peer-review specs/29-ship-it-dual-model-benchmark/ --model copilot:gpt-5.4` (consistency mode — peer-review auto-detects this from the directory target). Auto-approve every finding the reviewer classifies as valid; record skipped/declined findings inline with reason. Iteration cap 2 — re-run after applying iteration 1's findings, then stop regardless of whether iteration 2 introduced new findings. The cap is deliberately lower than Phase 9's cap of 4 because the surface area here is two short spec docs (no benchmark.json, benchmark.md, README, or cross-file drift to chase).
- [x] **0.3** Record per-iteration summary inline in this task. Format per spec-26/27/28 precedent: `Iteration N: K valid findings (X critical, Y major, Z minor). Applied all. {Brief note on themes.}`
  - Iteration 1 (copilot:gpt-5.4): 5 valid findings (1 critical, 3 major, 1 minor). Applied all. Themes: tasks.md inherited several spec-28 quirks that drifted from plan.md — (a) `with_skill` sandbox wording was self-contradictory (forbade reads outside the workspace AND required reading the parent-repo SKILL.md) and needed an explicit carve-out, (b) Phase 8 verifications were missing for the plan's sample-stddev (N−1) and signed-string `delta.*` requirements, (c) Per-Eval verification was a one-row spot check rather than the full 4-column × 3-eval grid, (d) `--branch` target was absent from the alt form of the Phase 9 command, (e) "Models tested" header verification said "run dates" instead of "date ranges". All from a literal copy of spec 28's tasks.md skeleton; spec 28 carried the same drift but the smaller surface area made it less consequential there.
  - Iteration 2 (copilot:gpt-5.4): 5 findings (0 critical, 4 major, 1 minor). Applied 4, declined 1. Applied: (a) sample-stddev verification needed 3-value subsets per configuration, not the merged 6-value set; (b) null-handling for aggregates (mean/stddev/min/max with `null` inputs) was unspecified — added explicit rule to plan.md and task 6.5; (c) eval_id verification was too narrow (only checked the historical mislabel) — broadened task 8.8 to validate every `(eval_id, eval_name)` pair against evals.json; (d) Phase 0.3 self-consistency — this iteration-2 summary added. Declined: "git worktree add flag position" finding — `git worktree add <path> -b <branch>` is valid git syntax (empirically verified in this session). Stopped after iteration 2 per cap.
- [x] **0.4** Commit the post-review spec docs as a single commit on the branch before Phase 1 begins. This commit is the start of the spec-29 PR; benchmark.json/benchmark.md/README.md changes from Phases 1–9 land as subsequent commits on the same branch.

---

## Phase 1: Schema reset and multi-model setup

- [x] **1.1** In `evals/ship-it/benchmark.json`, remove all 6 existing Sonnet runs from `runs[]` (entire `runs[]` array becomes empty until task 6.2 appends the new entries). Git history retains the prior shape; no in-file historical archive is kept.
- [x] **1.2** Reset `metadata.models_tested[]` to an empty array; entries are appended in Phase 6 (task 6.3) after grading.
- [x] **1.3** Set top-level `metadata.skill_version` to `"0.5"` (matches current `skills/ship-it/SKILL.md` `version`). This **backfills** the field — the prior benchmark.json had no `skill_version` recorded. Leave top-level `metadata.executor_model`, `metadata.analyzer_model`, and `metadata.timestamp` in place — they flip in Phase 6 (task 6.4) after Opus runs are graded.
- [x] **1.4** Set `metadata.evals_run` to `[1, 2, 4]` — corrects the prior `[1, 2, 3]` mislabel. The Phase 1 reset is the natural place to apply this fix because new entries are about to be appended with correct ids.
- [x] **1.5** Remove the existing top-level `run_summary` block (will be repopulated in Phase 6 from the new runs); add an empty `run_summary_by_model: {}` object.
- [x] **1.6** JSON-validate: `python3 -c 'import json; json.load(open("evals/ship-it/benchmark.json"))'`.
- [x] **1.7** Commit the schema reset as its own commit so the Phase 6 append (task 6.2) lands cleanly on top of an empty `runs[]` and an empty `models_tested[]`.

---

## Phase 2: Run Sonnet 4.6 v0.5 `with_skill`

- [x] **2.1** For each of the 3 evals (`evals.json` ids 1, 2, 4 — `bug-fix-null-check`, `draft-pr-wip-feature`, `refactor-with-branch-name`), spawn an executor subagent with `model: claude-sonnet-4-6` and configuration `with_skill`. Use the standard sandboxed-workspace pattern (`mktemp -d`, `cd` into it, write fixtures there). For `with_skill` runs, reading `skills/ship-it/SKILL.md` and `skills/ship-it/references/` from the parent repo is **explicitly permitted** — that read is what the skill being measured does. The "no reads outside the workspace" rule from `evals/CLAUDE.md` applies only to `without_skill` runs (Phase 3). **Do NOT call the `Skill` tool** — even for `with_skill`, the executor must follow `skills/ship-it/SKILL.md` directly (read it and act on its instructions); calling `Skill` delegates to a fresh sub-instance and is not what's being measured (per the executor rule in `evals/CLAUDE.md`). Capture transcripts for every run; record `tool_calls`, `errors`, `time_seconds`, `tokens`, and `cache_tokens` when the executor exposes them at the parent level, and record `null` when parent-level usage is not preserved (per specs 26/27/28's experience). Preserve raw outputs locally (transcripts + per-run summaries) — they are the source for Phase 6 grading.
- [x] **2.2** Sanity-scan results before grading: any run that finished in unexpectedly short time or produced an obviously malformed transcript is re-run before Phase 6.

---

## Phase 3: Run Sonnet 4.6 v0.5 `without_skill`

- [x] **3.1** Same 3 evals (ids 1, 2, 4), configuration `without_skill`, model `claude-sonnet-4-6`. Capture the same instrumentation as Phase 2. The `without_skill` executor must be explicitly forbidden from reading `skills/ship-it/SKILL.md` and `skills/ship-it/references/`, **and from calling the `Skill` tool** — register-and-invoke via the `Skill` tool contaminates the baseline even without SKILL.md reads (per `evals/CLAUDE.md`).
- [x] **3.2** Sanity-scan as in 2.2.

---

## Phase 4: Run Opus 4.7 `with_skill`

- [x] **4.1** For each of the 3 evals (ids 1, 2, 4), spawn an executor subagent with `model: claude-opus-4-7` and configuration `with_skill`. Same sandboxed-workspace and instrumentation rules as Phase 2 — including the explicit permission to read `skills/ship-it/SKILL.md` and `skills/ship-it/references/` from the parent repo. **Do NOT call the `Skill` tool**.
- [x] **4.2** Sanity-scan as in 2.2.

---

## Phase 5: Run Opus 4.7 `without_skill`

- [x] **5.1** Same 3 evals (ids 1, 2, 4), configuration `without_skill`, model `claude-opus-4-7`. Same forbid-rules as Phase 3 (no reads of `skills/ship-it/SKILL.md` or `skills/ship-it/references/`; no calls to the `Skill` tool).
- [x] **5.2** Sanity-scan as in 2.2.

---

## Phase 6: Grade and merge

- [x] **6.1** Grade all 12 transcripts (6 Sonnet + 6 Opus) against assertions from `evals/ship-it/evals.json`. **Sonnet 4.6 is the sole grader for all 12 transcripts — including the 6 Opus transcripts.** Each grader subagent is spawned with `model: claude-sonnet-4-6`; do not let the grader default to the executor's model, do not fall back to Opus for any subset, and do not switch analyzers partway through (the spec 26 mid-grading Opus → Sonnet fallback path is explicitly avoided here per the Analyzer-model choice section of plan.md). Produce a `grading.json`-shaped block per run with `summary` (passed/failed/total/pass_rate) and `expectations` (text/passed/evidence). Evidence paths must be repo-relative (no `/Users/...`). Use the grader subagent pattern from `evals/CLAUDE.md` — pass full assertion text strings (not assertion ids) to the grader. Record `analyzer_model: "claude-sonnet-4-6"` on every entry without exception.
- [x] **6.2** Append all 12 entries to `runs[]` in `evals/ship-it/benchmark.json`. Each entry has `executor_model` (`claude-sonnet-4-6` or `claude-opus-4-7`), `run_number: 1`, `eval_id` (1, 2, or 4 — **not** 3), `eval_name` (matching `evals.json`), `configuration` (`with_skill` or `without_skill`), `result` block (pass_rate, passed, failed, total, time_seconds, tokens, cache_tokens, tool_calls, errors — `tokens` is `input_tokens + output_tokens` and `cache_tokens` is `cache_creation_input_tokens + cache_read_input_tokens`, kept as separate fields per `evals/CLAUDE.md`), `expectations` array, and optional `notes`. Use `null` for any unknown time/token/cache_token/tool_call/error stats per the `evals/CLAUDE.md` rule.
- [x] **6.3** Append two blocks to `metadata.models_tested[]` — Sonnet first (chronologically), Opus second. Each block: `executor_model`, `analyzer_model: "claude-sonnet-4-6"`, `timestamp` (Phase 2/3 date for Sonnet block, Phase 4/5 date for Opus block), `skill_version: "0.5"`, `runs_per_configuration: 1`, `notes` string describing coverage (3 evals × 2 configs = 6 runs per model, all `run_number == 1`, deliberately chosen Sonnet analyzer for uniformity, eval 3 (`branch-name-collision`) excluded for fixture-cost reasons, any measurement-gap caveats).
- [x] **6.4** Flip top-level `metadata.executor_model` to `"claude-opus-4-7"` (latest-model convention from learn / pr-comments / peer-review / pr-human-guide); set top-level `metadata.analyzer_model` to `"claude-sonnet-4-6"` (deliberate-choice plan); update top-level `metadata.timestamp` to the Opus run date. Confirm `metadata.skill_version` is `"0.5"` (set in Phase 1).
- [x] **6.5** Compute `run_summary_by_model["claude-sonnet-4-6"]` from the 6 Sonnet runs. Filter `run_number: 1` (defensive; no other run_numbers exist). Compute `mean`, sample `stddev` (N−1), `min`, `max` for `pass_rate`, `time_seconds`, `tokens`, and `cache_tokens` (kept separate from `tokens` because cache reads/creation bill at different rates). **Null-handling**: exclude `null` values from each metric's sample; if a (configuration, metric) cell has no non-null values, set every field of that summary block to `null`. Compute `delta.pass_rate` at 2dp from unrounded means; compute `delta.time_seconds`, `delta.tokens`, and `delta.cache_tokens` as signed strings (per the `evals/CLAUDE.md` rule that all `run_summary.delta` values are signed strings). When either side of a delta has a null mean, set that `delta.<metric>` to `null` rather than a signed string.
- [x] **6.6** Compute `run_summary_by_model["claude-opus-4-7"]` from the 6 Opus runs using the same statistical formulas (including `cache_tokens` aggregates and delta).
- [x] **6.7** Update top-level `run_summary` to mirror `run_summary_by_model["claude-opus-4-7"]` (latest-model convention).
- [x] **6.8** JSON-validate: `python3 -c 'import json; json.load(open("evals/ship-it/benchmark.json"))'`.

---

## Phase 7: Update benchmark.md and README

- [x] **7.1** Update `evals/ship-it/benchmark.md` header: replace the single-model `**Model**: claude-sonnet-4-6` line with a **Models tested** section naming both models with date ranges (analogous to learn / pr-comments / peer-review / pr-human-guide format). Update the run-count summary line (3 evals × 2 configs × 2 models = 12 canonical runs, all at SKILL.md v0.5; eval 3 excluded — see Known Eval Limitations).
- [x] **7.2** Restructure the Summary section into per-model tables: one for `claude-sonnet-4-6`, one for `claude-opus-4-7`. Each table has rows for Pass rate / Time / Tokens (input + output) / Cache tokens (creation + reads), columns `with-skill | without-skill | Delta` with `±` stddev notation. Values match `run_summary_by_model` exactly.
- [x] **7.3** Update the Per-Eval Results section from 2 columns (Sonnet with/without) to 4 columns (Sonnet with, Sonnet without, Opus with, Opus without). Bold any 100% pass-rate cell; use `—` for null/missing instrumentation stats. Re-write the per-eval prose where Sonnet and Opus baselines diverge (mirror the eval 21/22 pattern from spec 26 Phase 7 iteration 4 and the eval 13/21 pattern from spec 27).
- [x] **7.4** Add or update "Known Eval Limitations" section: (a) for each model, list every eval id where both `with_skill` and `without_skill` pass rates are 1.0 (the non-discriminating set is determined by actual run results — record what's there, do not assume continuity from the prior baseline); (b) the version-unspecified → v0.5 skill-version reset rationale (existing Sonnet runs had no `skill_version` recorded and were re-run at v0.5 for apples-to-apples comparison) **plus** the eval_id-3 mislabel correction (prior runs had `eval_id: 3` for `refactor-with-branch-name`; correct id is 4); (c) eval 3 (`branch-name-collision`) gap with fixture-cost rationale and a flag as a candidate follow-up spec; (d) any Opus parent-level measurement gap encountered (per specs 26/27/28's experience).
- [x] **7.5** If the Opus 4.7 baseline meaningfully matches the skill on any eval (non-discriminating), flag it in the per-eval discussion as a candidate for future purpose-refresh work (do not rewrite in this spec — mirrors specs 25/26/27/28 pattern).
- [x] **7.6** Update `README.md` Available Skills table — ship-it `Eval Δ` column to show per-model deltas (e.g., `+38% Sonnet 4.6 / +M% Opus 4.7`) replacing the current single `+38%`.
- [x] **7.7** Update `README.md` ship-it Skill Notes `Eval cost` bullet with per-model time / tokens / pass-rate stats, mirroring the learn / pr-comments / peer-review / pr-human-guide format. Replace the current single-model `+41.0 seconds, +5,073 tokens over baseline` framing.

---

## Phase 8: Verify

- [x] **8.1** `python3 -c 'import json; json.load(open("evals/ship-it/benchmark.json"))'` — valid JSON.
- [x] **8.2** `jq '.runs | map(select(.executor_model == null)) | length' evals/ship-it/benchmark.json` — returns `0`.
- [x] **8.3** `jq '.runs | map(select(.eval_name == null)) | length' evals/ship-it/benchmark.json` — returns `0`.
- [x] **8.4** `jq '.runs | length' evals/ship-it/benchmark.json` — returns `12`.
- [x] **8.5** `jq '.metadata.models_tested | length' evals/ship-it/benchmark.json` — returns `2`.
- [x] **8.6** `jq -r '.metadata.skill_version' evals/ship-it/benchmark.json` matches the `version` value in `skills/ship-it/SKILL.md` (currently `0.5`).
- [x] **8.7** `jq '.metadata.evals_run' evals/ship-it/benchmark.json` — returns `[1, 2, 4]` (no eval id 3).
- [x] **8.8** Verify every `(eval_id, eval_name)` pair in `runs[]` matches `evals/ship-it/evals.json`, not just the historical eval_id-3 mislabel. Run:
  ```bash
  python3 -c '
  import json
  evals = {e["id"]: e["name"] for e in json.load(open("evals/ship-it/evals.json"))["evals"]}
  bench = json.load(open("evals/ship-it/benchmark.json"))
  bad = [(r["eval_id"], r["eval_name"]) for r in bench["runs"] if evals.get(r["eval_id"]) != r["eval_name"]]
  assert not bad, f"mismatched (eval_id, eval_name) pairs: {bad}"
  print("OK")
  '
  ```
  Expected output: `OK`. Catches any new mislabel beyond the eval_id-3 → eval_id-4 correction (e.g. swapped ids, typos in `eval_name`).
- [x] **8.9** `jq '.run_summary_by_model | keys' evals/ship-it/benchmark.json` — contains both `"claude-sonnet-4-6"` and `"claude-opus-4-7"`.
- [x] **8.10** `jq '.run_summary == .run_summary_by_model["claude-opus-4-7"]' evals/ship-it/benchmark.json` — returns `true` (top-level deep-equal to the latest-model summary, including `with_skill`, `without_skill`, and `delta`).
- [x] **8.10c** Verify sample-stddev (N−1) is used: for one model, separately recompute `with_skill.pass_rate.stddev` from the 3 `with_skill` `pass_rate` values and `without_skill.pass_rate.stddev` from the 3 `without_skill` `pass_rate` values via Python (`statistics.stdev(...)` uses N−1), and confirm both match `run_summary_by_model[<model>].<config>.pass_rate.stddev` to at least 4dp. Repeat for `time_seconds` over the same 3-value subsets when non-null values exist on both sides.
- [x] **8.10d** Verify all `delta.*` fields are signed strings, not numbers: `jq '[.run_summary_by_model[].delta | to_entries[] | select(.value | type != "string")] | length' evals/ship-it/benchmark.json` returns `0`. Same check on top-level `run_summary.delta`.
- [x] **8.11** Verify the Per-Eval Results table covers **all 3 eval rows** with the **4-column layout** (Sonnet with, Sonnet without, Opus with, Opus without): for each eval id (1, 2, 4) and each (model, configuration) cell, confirm the displayed pass-rate matches `jq '.runs[] | select(.eval_id == N and .executor_model == "<model>" and .configuration == "<config>") | .result.pass_rate'`. Three rows × four cells = 12 cells to confirm.
- [x] **8.12** README `Eval Δ` per-model values match `run_summary_by_model[<model>].delta.pass_rate` (rounded to nearest whole percent).
- [x] **8.12a** README ship-it Skill Notes `Eval cost` bullet shows per-model time / tokens / pass-rate deltas (no longer the single-model `+41.0 seconds, +5,073 tokens over baseline` framing). Values match `run_summary_by_model` for each model.
- [x] **8.12b** `benchmark.md` "Known Eval Limitations" section documents: (a) for each model, every eval id where both `with_skill` and `without_skill` pass rates are 1.0; (b) the version-unspecified → v0.5 skill-version reset rationale **plus** the eval_id-3 mislabel correction; (c) eval 3 (`branch-name-collision`) gap with fixture-cost rationale; (d) any Opus parent-level measurement gap encountered (or note explicitly if measurements were captured cleanly).
- [x] **8.13** `benchmark.md` "Models tested" header includes both models with date ranges (matches the wording in plan.md and Phase 7.1; if a model's runs span multiple days the header reflects the range).
- [x] **8.14** `benchmark.md` Summary-table `±` values match `run_summary_by_model` exactly. For each model and each row (Pass rate / Time / Tokens / Cache tokens), generate the expected display string with `jq -r '.run_summary_by_model["<model>"].with_skill.pass_rate | "\(.mean) ±\(.stddev)"' evals/ship-it/benchmark.json` (and the analogous `without_skill` and `time_seconds`/`tokens`/`cache_tokens` fields) and confirm it appears in `evals/ship-it/benchmark.md` (modulo formatting — e.g. `1.0 ±0.0` rendered as `100% ±0%`).
- [x] **8.15** `uv run --with pytest pytest tests/` — no regressions.
- [x] **8.16** `npx cspell README.md evals/ship-it/benchmark.md specs/29-ship-it-dual-model-benchmark/*.md` — clean; add new words to `cspell.config.yaml` in alphabetically-sorted position if needed.

---

## Phase 9: Peer review

*Fresh-context consistency pass before ship, to catch cross-file drift Phase 8's mechanical checks miss (stale deltas, Summary ± mismatches, `benchmark.md` vs `benchmark.json` drift, README deltas vs `run_summary_by_model`, plan.md ↔ tasks.md gaps). Exit condition: a pass produces zero valid findings. Iteration cap: 4.*

- [x] **9.1** Stage all spec-29 changes in the worktree.
- [x] **9.2** Run `/peer-review --branch evals/ship-it-opus-4-7-multi-model [--model <tool>]` and apply valid findings. Loop until zero valid findings or iteration cap 4. Record per-iteration summary inline in this task.
  - Iteration 1 (copilot:gpt-5.4): 2 findings (0 critical, 2 major, 0 minor). Applied 1, declined 1. Applied: Finding 2 — corrected prose in `evals/ship-it/benchmark.md` (Summary paragraph + eval 4 Per-Eval section + Opus 4.7 Notes) and `README.md` Skill Notes Eval cost bullet to describe the actual eval 4 Opus baseline failure (`## Summary` section *was* present, but contained only prose without bullets — bullets appeared under a separate `## Changes` heading), per the recorded `expectations[].evidence` in benchmark.json. Declined: Finding 1 — proposed relaxing the literal-string `## Summary` bullet assertion to a semantic-equivalence check and re-running, on grounds the +38% Opus headline is overstated. Out-of-scope per spec 29 (no assertion changes); the literal-string-vs-paraphrase pattern is already documented as a known limitation in `evals/CLAUDE.md` ("In multi-model benchmarks, literal-string assertions penalize paraphrase-prone models even when behavior is correct") and `benchmark.md` already calls out this Opus-specific output-quality variance explicitly. Candidate follow-up spec.
  - Iteration 2 (copilot:gpt-5.4): 2 findings (0 critical, 1 major, 1 minor). Applied both. Applied: (a) major — two `result.pass_rate` values stored as `0.62` instead of exact `5/8 = 0.625` (eval 2 Sonnet without_skill, eval 4 Opus without_skill); fixed both per-run values and recomputed `run_summary_by_model` and top-level `run_summary` from exact run data. The headline deltas held (`+0.29` Sonnet, `+0.38` Opus); the only downstream shift was Sonnet `without_skill` pass-rate stddev `±8% → ±7%` in benchmark.md's Summary table. (b) minor — eval 4 Opus prose still framed the `## Summary` failure as a "literal-string penalizes paraphrase" issue when the actual graded miss is structural (bullets present in the PR body but placed under `## Changes`, not under `## Summary` as the assertion requires). Reframed as "structural miss" and noted the skill corrects the placement.
  - Iteration 3 (copilot:gpt-5.4): 1 finding (0 critical, 0 major, 1 minor). Declined 1. Declined: claim that `cspell.config.yaml` `stdev` entry is out of alphabetical order — verified via `python3 -c "print(sorted(['stddev','stddevs','stdev']))"` that the current order (`stddev`, `stddevs`, `stdev`) is correct (position 4: `d` < `e`, so `stdd*` < `stde*`); the reviewer's claim that `stdev` should come *before* `stddev` is the inverse of the actual lexical order. Zero valid findings → exit condition met (iteration cap 4 not reached).

---

## Phase 10: Ship

- [x] **10.1** Commit all changes on branch `evals/ship-it-opus-4-7-multi-model`.
- [x] **10.2** Push and open PR; run `/pr-comments {pr_number}` immediately per CLAUDE.md post-push convention. (PR #133)
- [ ] **10.3** Loop `/pr-comments` until no new bot feedback.
- [ ] **10.4** Run `/pr-human-guide` to annotate the PR for human reviewers (per CLAUDE.md pre-merge rule; also dogfoods the skill that was benchmarked in spec 28).
- [ ] **10.5** Wait for human review. After approval: squash-merge via `gh pr merge --squash --delete-branch`, sync local main, remove the worktree directory.
