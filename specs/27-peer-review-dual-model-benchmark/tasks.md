# Spec 27: Tasks — peer-review dual-model benchmarking

## Phase 1: Schema upgrade (annotative, no new runs)

- [x] **1.1** In `evals/peer-review/benchmark.json`, add `metadata.models_tested[]` with a single Sonnet 4.6 block: `executor_model: "claude-sonnet-4-6"`, `analyzer_model: "claude-sonnet-4-6"`, `timestamp` matching existing top-level `timestamp` (`"2026-04-09T00:00:00Z"`), `runs_per_configuration: 1`, and a `notes` string describing the Sonnet coverage (28 evals × 2 configurations, eval 26 nulled on both sides due to contamination, 56 total runs all `run_number == 1`).
- [x] **1.2** Stamp `executor_model: "claude-sonnet-4-6"` on every entry in `runs[]`. Verify via `jq '.runs | map(select(.executor_model != "claude-sonnet-4-6")) | length' evals/peer-review/benchmark.json` returns `0`.
- [x] **1.3** Move the existing top-level `run_summary` into `run_summary_by_model["claude-sonnet-4-6"]` (keep the same mean/stddev/min/max/delta values — purely a key rename). Leave top-level `run_summary` in place, mirroring Sonnet for now; it flips to Opus in Phase 4.
- [x] **1.4** JSON-validate: `python3 -c 'import json; json.load(open("evals/peer-review/benchmark.json"))'`.
- [x] **1.5** Commit the schema upgrade as its own commit so Phase 4 runs append cleanly on top.

---

## Phase 2: Run Opus 4.7 `with_skill`

- [x] **2.1** For each of the 28 evals in `evals/peer-review/evals.json`, spawn an executor subagent with `model: claude-opus-4-7` and configuration `with_skill`. Capture transcripts, tool_calls, errors, time_seconds, tokens per run. Preserve raw outputs locally (transcripts + per-run summaries) — they are the source for Phase 3 grading. Use the standard sandboxed-workspace pattern (`mktemp -d`, no reads outside).
- [x] **2.2** Sanity-scan results before grading: any run that finished in unexpectedly short time or produced an obviously malformed transcript is re-run before Phase 4. Note that evals 5–10 and 15–28 use simulated transcripts (fixture CLI/triage responses embedded in the eval prompt) — short wall-clock time is expected for those, not anomalous.

---

## Phase 3: Run Opus 4.7 `without_skill`

- [x] **3.1** Same 28 evals, configuration `without_skill`, model `claude-opus-4-7`. Capture the same instrumentation as Phase 2. The `without_skill` executor must be explicitly forbidden from reading `skills/peer-review/SKILL.md` (this is the contamination vector that nulled Sonnet eval 26).
- [x] **3.2** Sanity-scan as in 2.2.
- [x] **3.3** Eval 26 contamination check: read the `without_skill` transcript for eval 26 and confirm the agent did not read `skills/peer-review/SKILL.md` and did not reproduce skill-defined error phrasing it could not have inferred. If clean, record normally. If contaminated, mark for paired-null treatment in Phase 4.

---

## Phase 4: Grade and merge

- [x] **4.1** Grade every Opus run (56 total) against assertions from `evals/peer-review/evals.json`. Produce a `grading.json`-shaped block per run with `summary` (passed/failed/total/pass_rate) and `expectations` (text/passed/evidence). Evidence paths must be repo-relative (no `/Users/...`). Use the grader subagent pattern from `evals/CLAUDE.md` — pass full assertion text strings (not assertion ids) to the grader. **Outcome:** Sonnet 4.6 was selected as the analyzer from the start for analyzer-uniformity (per spec 26 precedent); all 56 transcripts were graded by Sonnet — no rate-limit fallback was triggered.
- [x] **4.2** Append 56 new entries to `runs[]` in `evals/peer-review/benchmark.json`. Each entry has `executor_model: "claude-opus-4-7"`, `run_number: 1`, `eval_name`, `result` block (pass_rate, passed, failed, total, time_seconds, tokens, tool_calls, errors), `expectations` array, and optional `notes`. Use `null` for any unknown time/token/tool_call/error stats per the `evals/CLAUDE.md` rule. If eval 26 Opus `without_skill` was contaminated (per task 3.3), null all result fields and expectations on **both** Opus sides for paired-eval consistency, mirroring the Sonnet treatment.
- [x] **4.3** Append an Opus 4.7 block to `metadata.models_tested[]`: `executor_model: "claude-opus-4-7"`, `analyzer_model: "claude-sonnet-4-6"` (the deliberately chosen analyzer per the from-the-start plan in 4.1), current timestamp, `runs_per_configuration: 1`, notes string describing coverage, the deliberately chosen Sonnet analyzer, and the eval 26 outcome.
- [x] **4.4** Flip top-level `metadata.executor_model` to `"claude-opus-4-7"` (latest-model convention from learn / pr-comments); set top-level `metadata.analyzer_model` to `"claude-sonnet-4-6"` (per the deliberate-choice plan; analyzer is Sonnet 4.6 even though executor is Opus 4.7). Update top-level `metadata.timestamp` to the Opus run date. Set `metadata.skill_version` explicitly to the current SKILL.md version (verify with `rg '^  version:' skills/peer-review/SKILL.md`).
- [x] **4.5** Compute `run_summary_by_model["claude-opus-4-7"]` from Opus runs. Filter `run_number: 1` only (defensive — peer-review has only run_number==1, but mirror the spec 26 pattern). Exclude eval 26 from aggregates only if it was nulled on both Opus sides; otherwise include it (delta computed over 28 paired evals on the Opus side; document the Sonnet/Opus paired-eval-count asymmetry in benchmark.md). Compute `mean`, sample `stddev` (N−1), `min`, `max` for `pass_rate`, `time_seconds`, `tokens`. Compute `delta.pass_rate` at 2dp from unrounded means.
- [x] **4.6** Recompute `run_summary_by_model["claude-sonnet-4-6"]` on the same `run_number: 1` filter for parity (excluding eval 26 — this matches the existing computation). Verify the recomputed values match the existing `+0.26` headline; if any value shifts, surface it in `benchmark.md` rather than overwriting silently.
- [x] **4.7** Update top-level `run_summary` to mirror `run_summary_by_model["claude-opus-4-7"]` (latest-model convention).
- [x] **4.8** JSON-validate.

---

## Phase 5: Update benchmark.md and README

- [x] **5.1** Update `evals/peer-review/benchmark.md` header: replace the single-model `**Model**: claude-sonnet-4-6` line with a **Models tested** section naming both models with date ranges (analogous to learn / pr-comments format). Update the run-count summary line (28 evals × 2 configs × 2 models = 112 canonical runs; eval 26 nulled on Sonnet, and on Opus iff contaminated).
- [x] **5.2** Restructure the Summary section into per-model tables: one for `claude-sonnet-4-6`, one for `claude-opus-4-7`. Each table has rows for Pass rate / Time / Tokens, columns `with-skill | without-skill | Delta` with `±` stddev notation. Values match `run_summary_by_model` exactly.
- [x] **5.3** Update the Per-Eval Results sections from 2 columns (Sonnet with/without) to 4 columns (Sonnet with, Sonnet without, Opus with, Opus without) — or add an Opus column-set per-eval block. Bold any 100% pass-rate cell; use `—` or omit bold for null/missing instrumentation stats. The existing per-eval prose can stay; add per-model qualifiers where Sonnet and Opus baselines diverge (mirror the eval 21/22 pattern from spec 26 Phase 7 iteration 4).
- [x] **5.4** Add or update "Notes" / "Known Eval Limitations" section: (a) Opus 4.7 non-discriminating cells listed by eval id, (b) Sonnet 4.6 sparse time/token coverage (time + tokens both have 7 of 27 paired primary runs measured: evals 1, 3, 4, 11, 12, 13, 14) called out, (c) Opus measurement gap (parent-level usage not captured per spec 26 experience), (d) the eval 26 contamination decision. **Outcome:** Opus ran cleanly on eval 26 — Opus paired-eval count is 28; Sonnet remains 27 (eval 26 nulled on both Sonnet sides). The "OR paired-null on contamination" branch did not apply.
- [x] **5.5** If the Opus 4.7 baseline meaningfully matches the skill on any eval (non-discriminating), flag it in the per-eval discussion as a candidate for future purpose-refresh work (do not rewrite in this spec — mirrors specs 25/26 pattern).
- [x] **5.6** Update `README.md` Available Skills table — peer-review `Eval Δ` column to show per-model deltas (e.g., `+26% Sonnet 4.6 / +N% Opus 4.7`).
- [x] **5.7** Update `README.md` peer-review Skill Notes `Eval cost` bullet with per-model time / tokens / pass-rate stats, mirroring the learn / pr-comments format.

---

## Phase 6: Verify

- [x] **6.1** `python3 -c 'import json; json.load(open("evals/peer-review/benchmark.json"))'` — valid JSON.
- [x] **6.2** `jq '.runs | map(select(.executor_model == null)) | length' evals/peer-review/benchmark.json` — returns `0`.
- [x] **6.3** `jq '.runs | map(select(.eval_name == null)) | length' evals/peer-review/benchmark.json` — returns `0`.
- [x] **6.4** `jq '.metadata.models_tested | length' evals/peer-review/benchmark.json` — returns `2`.
- [x] **6.5** `jq -r '.metadata.skill_version' evals/peer-review/benchmark.json` matches `version` in `skills/peer-review/SKILL.md`.
- [x] **6.6** `jq '.run_summary_by_model | keys' evals/peer-review/benchmark.json` — contains both `"claude-sonnet-4-6"` and `"claude-opus-4-7"`.
- [x] **6.7** `jq '.run_summary.pass_rate.with_skill.mean == .run_summary_by_model["claude-opus-4-7"].pass_rate.with_skill.mean' evals/peer-review/benchmark.json` — returns `true` (top-level mirrors latest model).
- [x] **6.8** Spot-check one eval's Per-Eval Results row in `benchmark.md` against `jq '.runs[] | select(.eval_id == N and .executor_model == "claude-opus-4-7")'` output — values must match.
- [x] **6.9** README `Eval Δ` per-model values match `run_summary_by_model[<model>].delta.pass_rate` (rounded to nearest whole percent).
- [x] **6.10** `benchmark.md` "Models tested" header includes Opus 4.7 with the run date.
- [x] **6.11** `benchmark.md` Summary-table `±` values match `run_summary_by_model` exactly (visual spot-check).
- [x] **6.12** Eval 26 row in `benchmark.md`: shows `N/A | — | —` on both Sonnet sides, and on Opus sides iff the Opus without_skill was contaminated. Otherwise Opus row shows real values.
- [x] **6.13** `uv run --with pytest pytest tests/` — no regressions.
- [x] **6.14** `npx cspell README.md evals/peer-review/benchmark.md specs/27-peer-review-dual-model-benchmark/*.md` — clean; add new words to `cspell.config.yaml` in sorted position if needed.

---

## Phase 7: Peer review

*Fresh-context consistency pass before ship, to catch cross-file drift Phase 6's mechanical checks miss (stale deltas, Summary ± mismatches, `benchmark.md` vs `benchmark.json` drift, README deltas vs `run_summary_by_model`, plan.md ↔ tasks.md gaps). Exit condition: a pass produces zero valid findings. Iteration cap: 4.*

- [x] **7.1** Stage all spec-27 changes in the worktree.
- [x] **7.2** Run `/peer-review --branch evals/peer-review-opus-4-7-multi-model` (or `/peer-review --model <tool>`) and apply valid findings. Loop until zero valid findings or iteration cap 4. Record per-iteration summary inline in this task.
  - **Iteration 1**: 8 valid findings (1 critical, 4 major, 3 minor). Critical: "Ten evals" / "11 evals" mismatch in Opus `models_tested[].notes`. Major: per-eval qualifiers stale on evals 6/12/18/22/23/24/25, eval 26 prose Sonnet-only, eval 13 collapse omits with-skill regression, Sonnet `Models tested` missing version qualifier. Minor: spec doc analyzer-fallback narrative, task 5.4 outcome annotation, task 4.2 unused `notes` mention. All 8 applied across `benchmark.json`, `benchmark.md`, `plan.md`, `tasks.md`.
  - **Iteration 2 (re-scan)**: 3 valid findings (2 major, 1 minor). Caught drift introduced by iteration 1 apply: `plan.md` Risks section "Analyzer-model fallback risk" still framed as fallback, tasks 4.3/4.4 still described fallback, skill-version qualifier added in 3 places now redundant with standalone Skill version paragraph. All 3 applied.
  - **Iteration 3 (re-scan)**: not run — re-scan offered at most once per peer-review skill rule. Exit condition met: zero valid findings on the re-scan apply path.

---

## Phase 8: Ship

- [ ] **8.1** Commit all changes on branch `evals/peer-review-opus-4-7-multi-model`.
- [ ] **8.2** Push and open PR; run `/pr-comments {pr_number}` immediately per CLAUDE.md post-push convention.
- [ ] **8.3** Loop `/pr-comments` until no new bot feedback.
- [ ] **8.4** Run `/pr-human-guide` to annotate the PR for human reviewers (per CLAUDE.md pre-merge rule).
- [ ] **8.5** Wait for human review. After approval: squash-merge via `gh pr merge --squash --delete-branch`, sync local main, remove the worktree directory.
