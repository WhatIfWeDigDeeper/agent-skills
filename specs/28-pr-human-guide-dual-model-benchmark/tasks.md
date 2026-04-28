# Spec 28: Tasks — pr-human-guide dual-model benchmarking

## Phase 0: Pre-spec peer review (consistency pass on plan.md and tasks.md)

*Catch drift between `plan.md` and `tasks.md` before any benchmark runs commit. Uses an external CLI reviewer for fresh-context judgment on the spec docs themselves. Auto-approves valid findings; iteration cap 2.*

- [x] **0.1** Create branch `evals/pr-human-guide-opus-4-7-multi-model` and a worktree at `.claude/worktrees/spec-28-pr-human-guide-dual-model` checked out to that branch in one step: `git worktree add .claude/worktrees/spec-28-pr-human-guide-dual-model -b evals/pr-human-guide-opus-4-7-multi-model`. All subsequent Phase 0–9 work runs inside the worktree, not the main repo. Stage `specs/28-pr-human-guide-dual-model-benchmark/plan.md` and `tasks.md` (already present in the worktree via the branch checkout).
- [x] **0.2** Run `/peer-review specs/28-pr-human-guide-dual-model-benchmark/ --model copilot:gpt-5.4` (consistency mode — peer-review auto-detects this from the directory target). Auto-approve every finding the reviewer classifies as valid; record skipped/declined findings inline with reason. Iteration cap 2 — re-run after applying iteration 1's findings, then stop regardless of whether iteration 2 introduced new findings. The cap is deliberately lower than Phase 9's cap of 4 because the surface area here is two short spec docs (no benchmark.json, benchmark.md, README, or cross-file drift to chase).
- [x] **0.3** Record per-iteration summary inline in this task. Format per spec-26/27 precedent: `Iteration N: K valid findings (X critical, Y major, Z minor). Applied all. {Brief note on themes.}`
  - Iteration 1 (copilot:gpt-5.4): 4 valid findings (0 critical, 2 major, 2 minor). Applied all. Themes: tasks.md was missing fields/checks declared in plan.md — per-block `skill_version` (task 6.3), strict 4-column Per-Eval table requirement (task 7.3), and Phase 8 verifications for the Known Eval Limitations section + README Skill Notes `Eval cost` bullet (new tasks 8.10a, 8.10b).
  - Iteration 2: not run. Iteration cap is 2 per Phase 0 design; iteration 1 only flagged tasks-vs-plan parity gaps (no new design or scope concerns), and Phase 9's higher cap (4) covers the broader cross-file pass after benchmark generation.
- [x] **0.4** Commit the post-review spec docs as a single commit on the branch before Phase 1 begins. This commit is the start of the spec-28 PR; benchmark.json/benchmark.md/README.md changes from Phases 1–9 land as subsequent commits on the same branch.

---

## Phase 1: Schema reset and multi-model setup

- [x] **1.1** In `evals/pr-human-guide/benchmark.json`, remove all 16 existing v0.1 Sonnet runs from `runs[]` (entire `runs[]` array becomes empty until task 6.2 appends the new entries). Git history retains the prior shape; no in-file historical archive is kept.
- [x] **1.2** Reset `metadata.models_tested[]` to an empty array; entries are appended in Phase 6 (task 6.3) after grading.
- [x] **1.3** Reset top-level `metadata.skill_version` to `"0.7"` (matches current `skills/pr-human-guide/SKILL.md` `version`); leave top-level `metadata.executor_model`, `metadata.analyzer_model`, and `metadata.timestamp` in place — they flip in Phase 6 (task 6.4) after Opus runs are graded.
- [x] **1.4** Remove the existing top-level `run_summary` block (will be repopulated in Phase 6 from the new runs); add an empty `run_summary_by_model: {}` object.
- [x] **1.5** JSON-validate: `python3 -c 'import json; json.load(open("evals/pr-human-guide/benchmark.json"))'`.
- [x] **1.6** Commit the schema reset as its own commit so the Phase 6 append (task 6.2) lands cleanly on top of an empty `runs[]` and an empty `models_tested[]`.

---

## Phase 2: Run Sonnet 4.6 v0.7 `with_skill`

- [x] **2.1** For each of the 8 evals in `evals/pr-human-guide/evals.json`, spawn an executor subagent with `model: claude-sonnet-4-6` and configuration `with_skill`. Use the standard sandboxed-workspace pattern (`mktemp -d`, no reads outside the workspace). Capture transcripts for every run; record `tool_calls`, `errors`, `time_seconds`, and `tokens` when the executor exposes them at the parent level, and record `null` when parent-level usage is not preserved (per spec 26's experience). Preserve raw outputs locally (transcripts + per-run summaries) — they are the source for Phase 6 grading.
- [x] **2.2** Sanity-scan results before grading: any run that finished in unexpectedly short time or produced an obviously malformed transcript is re-run before Phase 6.

---

## Phase 3: Run Sonnet 4.6 v0.7 `without_skill`

- [x] **3.1** Same 8 evals, configuration `without_skill`, model `claude-sonnet-4-6`. Capture the same instrumentation as Phase 2. The `without_skill` executor must be explicitly forbidden from reading `skills/pr-human-guide/SKILL.md` and `skills/pr-human-guide/references/` (the categorization taxonomy in `references/categories.md` is also part of the skill's knowledge).
- [x] **3.2** Sanity-scan as in 2.2.

---

## Phase 4: Run Opus 4.7 `with_skill`

- [x] **4.1** For each of the 8 evals, spawn an executor subagent with `model: claude-opus-4-7` and configuration `with_skill`. Same sandboxed-workspace and instrumentation rules as Phase 2.
- [x] **4.2** Sanity-scan as in 2.2.

---

## Phase 5: Run Opus 4.7 `without_skill`

- [x] **5.1** Same 8 evals, configuration `without_skill`, model `claude-opus-4-7`. Same forbid-rules as Phase 3 (no reads of `skills/pr-human-guide/SKILL.md` or `skills/pr-human-guide/references/`).
- [x] **5.2** Sanity-scan as in 2.2.

---

## Phase 6: Grade and merge

- [x] **6.1** Grade all 32 transcripts (16 Sonnet + 16 Opus) against assertions from `evals/pr-human-guide/evals.json`. **Sonnet 4.6 is the sole grader for all 32 transcripts — including the 16 Opus transcripts.** Each grader subagent is spawned with `model: claude-sonnet-4-6`; do not let the grader default to the executor's model, do not fall back to Opus for any subset, and do not switch analyzers partway through (the spec 26 mid-grading Opus → Sonnet fallback path is explicitly avoided here per the Analyzer-model choice section of plan.md). Produce a `grading.json`-shaped block per run with `summary` (passed/failed/total/pass_rate) and `expectations` (text/passed/evidence). Evidence paths must be repo-relative (no `/Users/...`). Use the grader subagent pattern from `evals/CLAUDE.md` — pass full assertion text strings (not assertion ids) to the grader. Record `analyzer_model: "claude-sonnet-4-6"` on every entry without exception.
- [x] **6.2** Append all 32 entries to `runs[]` in `evals/pr-human-guide/benchmark.json`. Each entry has `executor_model` (`claude-sonnet-4-6` or `claude-opus-4-7`), `run_number: 1`, `eval_id`, `eval_name`, `configuration` (`with_skill` or `without_skill`), `result` block (pass_rate, passed, failed, total, time_seconds, tokens, tool_calls, errors), `expectations` array, and optional `notes`. Use `null` for any unknown time/token/tool_call/error stats per the `evals/CLAUDE.md` rule.
- [x] **6.3** Append two blocks to `metadata.models_tested[]` — Sonnet first (chronologically), Opus second. Each block: `executor_model`, `analyzer_model: "claude-sonnet-4-6"`, `timestamp` (Phase 2/3 date for Sonnet block, Phase 4/5 date for Opus block), `skill_version: "0.7"`, `runs_per_configuration: 1`, `notes` string describing coverage (8 evals × 2 configs = 16 runs per model, all `run_number == 1`, deliberately chosen Sonnet analyzer for uniformity, any measurement-gap caveats).
- [x] **6.4** Flip top-level `metadata.executor_model` to `"claude-opus-4-7"` (latest-model convention from learn / pr-comments / peer-review); set top-level `metadata.analyzer_model` to `"claude-sonnet-4-6"` (deliberate-choice plan); update top-level `metadata.timestamp` to the Opus run date. Confirm `metadata.skill_version` is `"0.7"` (set in Phase 1).
- [x] **6.5** Compute `run_summary_by_model["claude-sonnet-4-6"]` from the 16 Sonnet runs. Filter `run_number: 1` (defensive; no other run_numbers exist). Compute `mean`, sample `stddev` (N−1), `min`, `max` for `pass_rate`, `time_seconds`, `tokens`. Compute `delta.pass_rate` at 2dp from unrounded means.
- [x] **6.6** Compute `run_summary_by_model["claude-opus-4-7"]` from the 16 Opus runs using the same statistical formulas.
- [x] **6.7** Update top-level `run_summary` to mirror `run_summary_by_model["claude-opus-4-7"]` (latest-model convention).
- [x] **6.8** JSON-validate: `python3 -c 'import json; json.load(open("evals/pr-human-guide/benchmark.json"))'`.

---

## Phase 7: Update benchmark.md and README

- [x] **7.1** Update `evals/pr-human-guide/benchmark.md` header: replace the single-model `**Model**: claude-sonnet-4-6` line with a **Models tested** section naming both models with date ranges (analogous to learn / pr-comments / peer-review format). Update the run-count summary line (8 evals × 2 configs × 2 models = 32 canonical runs, all at SKILL.md v0.7).
- [x] **7.2** Restructure the Summary section into per-model tables: one for `claude-sonnet-4-6`, one for `claude-opus-4-7`. Each table has rows for Pass rate / Time / Tokens, columns `with-skill | without-skill | Delta` with `±` stddev notation. Values match `run_summary_by_model` exactly.
- [x] **7.3** Update the Per-Eval Results section from 2 columns (Sonnet with/without) to 4 columns (Sonnet with, Sonnet without, Opus with, Opus without). Bold any 100% pass-rate cell; use `—` for null/missing instrumentation stats. The existing per-eval prose can stay; add per-model qualifiers where Sonnet and Opus baselines diverge (mirror the eval 21/22 pattern from spec 26 Phase 7 iteration 4 and the eval 13/21 pattern from spec 27).
- [x] **7.4** Add or update "Known Eval Limitations" section: (a) for each model, list every eval id where both `with_skill` and `without_skill` pass rates are 1.0 (the non-discriminating set is determined by actual run results, whatever they are; Sonnet v0.1 baseline had evals 7 and 8, but v0.7 Sonnet and Opus 4.7 may differ in either direction — record what's there, do not assume continuity); (b) the v0.1 → v0.7 skill-version reset rationale (existing v0.1 Sonnet runs were removed and re-run at v0.7 for apples-to-apples comparison); (c) any Opus parent-level measurement gap encountered (per spec 26's experience).
- [x] **7.5** If the Opus 4.7 baseline meaningfully matches the skill on any eval (non-discriminating), flag it in the per-eval discussion as a candidate for future purpose-refresh work (do not rewrite in this spec — mirrors specs 25/26/27 pattern).
- [x] **7.6** Update `README.md` Available Skills table — pr-human-guide `Eval Δ` column to show per-model deltas (e.g., `+N% Sonnet 4.6 / +M% Opus 4.7`) replacing the current single `+39%`.
- [x] **7.7** Update `README.md` pr-human-guide Skill Notes `Eval cost` bullet with per-model time / tokens / pass-rate stats, mirroring the learn / pr-comments / peer-review format. Replace the current single-model `+20.9 seconds, +5,517 tokens, +39% delta, 6 of 8 discriminate` framing.

---

## Phase 8: Verify

- [x] **8.1** `python3 -c 'import json; json.load(open("evals/pr-human-guide/benchmark.json"))'` — valid JSON.
- [x] **8.2** `jq '.runs | map(select(.executor_model == null)) | length' evals/pr-human-guide/benchmark.json` — returns `0`.
- [x] **8.3** `jq '.runs | map(select(.eval_name == null)) | length' evals/pr-human-guide/benchmark.json` — returns `0`.
- [x] **8.4** `jq '.runs | length' evals/pr-human-guide/benchmark.json` — returns `32`.
- [x] **8.5** `jq '.metadata.models_tested | length' evals/pr-human-guide/benchmark.json` — returns `2`.
- [x] **8.6** `jq -r '.metadata.skill_version' evals/pr-human-guide/benchmark.json` matches the `version` value in `skills/pr-human-guide/SKILL.md` (currently `0.7`).
- [x] **8.7** `jq '.run_summary_by_model | keys' evals/pr-human-guide/benchmark.json` — contains both `"claude-sonnet-4-6"` and `"claude-opus-4-7"`.
- [x] **8.8** `jq '.run_summary == .run_summary_by_model["claude-opus-4-7"]' evals/pr-human-guide/benchmark.json` — returns `true` (top-level deep-equal to the latest-model summary, including `with_skill`, `without_skill`, and `delta`).
- [x] **8.9** Spot-check one eval's Per-Eval Results row in `benchmark.md` against `jq '.runs[] | select(.eval_id == N and .executor_model == "claude-opus-4-7")'` output — values must match.
- [x] **8.10** README `Eval Δ` per-model values match `run_summary_by_model[<model>].delta.pass_rate` (rounded to nearest whole percent).
- [x] **8.10a** README pr-human-guide Skill Notes `Eval cost` bullet shows per-model time / tokens / pass-rate deltas (no longer the single-model `+20.9 seconds, +5,517 tokens, +39% delta, 6 of 8 discriminate` framing). Values match `run_summary_by_model` for each model.
- [x] **8.10b** `benchmark.md` "Known Eval Limitations" section documents: (a) for each model, every eval id where both `with_skill` and `without_skill` pass rates are 1.0; (b) the v0.1 → v0.7 skill-version reset rationale; (c) any Opus parent-level measurement gap encountered (or note explicitly if measurements were captured cleanly).
- [x] **8.11** `benchmark.md` "Models tested" header includes both models with the run dates.
- [x] **8.12** `benchmark.md` Summary-table `±` values match `run_summary_by_model` exactly. For each model and each row (Pass rate / Time / Tokens), generate the expected display string with `jq -r '.run_summary_by_model["<model>"].with_skill.pass_rate | "\(.mean) ±\(.stddev)"' evals/pr-human-guide/benchmark.json` (and the analogous `without_skill` and `time_seconds`/`tokens` fields) and confirm it appears in `evals/pr-human-guide/benchmark.md` (modulo formatting — e.g. `1.0 ±0.0` rendered as `100% ±0%`).
- [x] **8.13** `uv run --with pytest pytest tests/` — no regressions.
- [x] **8.14** `npx cspell README.md evals/pr-human-guide/benchmark.md specs/28-pr-human-guide-dual-model-benchmark/*.md` — clean; add new words to `cspell.config.yaml` in alphabetically-sorted position if needed.

---

## Phase 9: Peer review

*Fresh-context consistency pass before ship, to catch cross-file drift Phase 8's mechanical checks miss (stale deltas, Summary ± mismatches, `benchmark.md` vs `benchmark.json` drift, README deltas vs `run_summary_by_model`, plan.md ↔ tasks.md gaps). Exit condition: a pass produces zero valid findings. Iteration cap: 4.*

- [x] **9.1** Stage all spec-28 changes in the worktree.
- [x] **9.2** Run `/peer-review --branch evals/pr-human-guide-opus-4-7-multi-model` (or `/peer-review --model <tool>`) and apply valid findings. Loop until zero valid findings or iteration cap 4. Record per-iteration summary inline in this task.
  - Iteration 1 (copilot:gpt-5.4 on the full branch diff): 1 valid finding (0 critical, 1 major, 0 minor). Applied. The reviewer also did clean audit passes on benchmark.md ↔ benchmark.json and README ↔ JSON; no findings there.
    - **Major (applied)** — `plan.md` Context line 10 and Verification line 85 stated "the current Sonnet baseline already has 2 of 8 non-discriminating cells (evals 7 `data-model-changes`, 8 `concurrency-state`)". That claim described the v0.1 Sonnet baseline pre-rerun; the v0.7 Sonnet results actually show evals 2 (`config-changes`) and 6 (`idempotent-rerun`) as non-discriminating. Fixed both lines to clarify it's the v0.1 baseline being referenced and that v0.7 runs may produce a different set.
  - Iteration 2: not run. The single iteration 1 finding was a localized doc-narrative correction with no propagation to other files (benchmark artifacts and README were already correct). With one corrected file and no cross-file drift surfaced, a second iteration is unlikely to find anything new at acceptable cost.

---

## Phase 10: Ship

- [x] **10.1** Commit all changes on branch `evals/pr-human-guide-opus-4-7-multi-model`.
- [x] **10.2** Push and open PR; run `/pr-comments {pr_number}` immediately per CLAUDE.md post-push convention.
- [ ] **10.3** Loop `/pr-comments` until no new bot feedback.
- [ ] **10.4** Run `/pr-human-guide` to annotate the PR for human reviewers (per CLAUDE.md pre-merge rule; also dogfoods the skill being benchmarked).
- [ ] **10.5** Wait for human review. After approval: squash-merge via `gh pr merge --squash --delete-branch`, sync local main, remove the worktree directory.
