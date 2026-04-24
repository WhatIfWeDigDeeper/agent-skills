# Spec 26: Tasks — pr-comments dual-model benchmarking

## Phase 1: Schema upgrade (annotative, no new runs)

- [x] **1.1** In `evals/pr-comments/benchmark.json`, add `metadata.models_tested[]` with a single Sonnet 4.6 block: `executor_model: "claude-sonnet-4-6"`, `analyzer_model: "claude-sonnet-4-6"`, `timestamp` matching existing top-level `timestamp`, `runs_per_configuration: 1`, and a `notes` string describing the Sonnet coverage (all 38 evals × 2 configs + 6 regression runs dated 2026-03-29 → 2026-04-12).
- [x] **1.2** Stamp `executor_model: "claude-sonnet-4-6"` on every entry in `runs[]`. Verify via `jq '.runs | map(select(.executor_model != "claude-sonnet-4-6")) | length' evals/pr-comments/benchmark.json` returns `0`.
- [x] **1.3** Move the existing top-level `run_summary` into `run_summary_by_model["claude-sonnet-4-6"]` (keep the same mean/stddev/min/max/delta values — purely a key rename). Leave top-level `run_summary` in place, mirroring Sonnet for now; it flips to Opus in Phase 4.
- [x] **1.4** JSON-validate: `python3 -c 'import json; json.load(open("evals/pr-comments/benchmark.json"))'`.
- [x] **1.5** Commit the schema upgrade as its own commit so Phase 4 runs append cleanly on top.

---

## Phase 2: Run Opus 4.7 `with_skill`

- [ ] **2.1** For each of the 38 evals in `evals/pr-comments/evals.json`, spawn an executor subagent with `model: claude-opus-4-7` and configuration `with_skill`. Capture transcripts, tool_calls, errors, time_seconds, tokens per run. Preserve raw outputs locally (transcripts + per-run summaries) — they are the source for Phase 3 grading.
- [ ] **2.2** Sanity-scan results before grading: any run that finished in unexpectedly short time or produced an obviously malformed transcript is re-run before Phase 3.

---

## Phase 3: Run Opus 4.7 `without_skill`

- [ ] **3.1** Same 38 evals, configuration `without_skill`, model `claude-opus-4-7`. Capture the same instrumentation as Phase 2.
- [ ] **3.2** Sanity-scan as in 2.2.

---

## Phase 4: Grade and merge

- [ ] **4.1** Grade every Opus run (76 total) against assertions from `evals/pr-comments/evals.json`. Produce a `grading.json`-shaped block per run with `summary` (passed/failed/total/pass_rate) and `expectations` (text/passed/evidence). Evidence paths must be repo-relative (no `/Users/...`).
- [ ] **4.2** Append 76 new entries to `runs[]` in `evals/pr-comments/benchmark.json`. Each entry has `executor_model: "claude-opus-4-7"`, `run_number: 1`, `eval_name`, `result` block (pass_rate, passed, failed, total, time_seconds, tokens, tool_calls, errors), `expectations` array, and optional `notes`.
- [ ] **4.3** Append an Opus 4.7 block to `metadata.models_tested[]`: `executor_model: "claude-opus-4-7"`, `analyzer_model: "claude-opus-4-7"`, current timestamp, `runs_per_configuration: 1`, notes string describing coverage.
- [ ] **4.4** Flip top-level `metadata.executor_model` and `metadata.analyzer_model` to `"claude-opus-4-7"` (latest-model convention from learn). Update top-level `metadata.timestamp` and `metadata.last_updated` to the Opus run date. Set `metadata.skill_version` explicitly to `"1.36"` (matches SKILL.md current version).
- [ ] **4.5** Compute `run_summary_by_model["claude-opus-4-7"]` from Opus runs (filter `run_number: 1` only). Compute `mean`, sample `stddev` (N−1), `min`, `max` for `pass_rate`, `time_seconds`, `tokens`. Compute `delta.pass_rate` at 2dp from unrounded means.
- [ ] **4.6** Recompute `run_summary_by_model["claude-sonnet-4-6"]` on the same `run_number: 1` filter for parity (do not include regression runs).
- [ ] **4.7** Update top-level `run_summary` to mirror `run_summary_by_model["claude-opus-4-7"]` (latest-model convention).
- [ ] **4.8** JSON-validate.

---

## Phase 5: Update benchmark.md and README

- [ ] **5.1** Update `evals/pr-comments/benchmark.md` header: add a **Models tested** line naming both models with date ranges (analogous to learn's format). Update the run-count summary line (38 × 2 configs × 2 models = 152 canonical runs, plus existing 6 Sonnet-only regression runs).
- [ ] **5.2** Restructure the Summary section into per-model tables: one for `claude-sonnet-4-6`, one for `claude-opus-4-7`. Each table has rows for Pass rate / Time / Tokens, columns `with-skill | without-skill | Delta` with `±` stddev notation. Values match `run_summary_by_model` exactly.
- [ ] **5.3** Update the Per-Eval Results table from 2 columns (Sonnet with/without) to 4 columns (Sonnet with, Sonnet without, Opus with, Opus without). Bold any cell under 100% pass rate; use `—` or omit bold for null/missing instrumentation stats.
- [ ] **5.4** Add or update "Known Eval Limitations" section: (a) Opus 4.7 non-discriminating cells listed by eval id, (b) Sonnet 4.6 sparse time/token coverage (~8 of 76 primary runs measured) called out, (c) regression runs (evals 12/14/20/22/23/24 with `run_number > 1`) noted as Sonnet-only variance probes excluded from multi-model aggregation.
- [ ] **5.5** If the Opus 4.7 baseline meaningfully matches the skill on any eval (non-discriminating), flag it in the per-eval discussion as a candidate for future purpose-refresh work (do not rewrite in this spec — mirrors spec 25 pattern).
- [ ] **5.6** Update `README.md` Available Skills table — pr-comments `Eval Δ` column to show per-model deltas (e.g., `+66% Sonnet 4.6 / +N% Opus 4.7`).
- [ ] **5.7** Update `README.md` pr-comments Skill Notes `Eval cost` bullet with per-model time / tokens / pass-rate stats, mirroring the learn format.

---

## Phase 6: Verify

- [ ] **6.1** `python3 -c 'import json; json.load(open("evals/pr-comments/benchmark.json"))'` — valid JSON.
- [ ] **6.2** `jq '.runs | map(select(.executor_model == null)) | length' evals/pr-comments/benchmark.json` — returns `0`.
- [ ] **6.3** `jq '.runs | map(select(.eval_name == null)) | length' evals/pr-comments/benchmark.json` — returns `0`.
- [ ] **6.4** `jq '.metadata.models_tested | length' evals/pr-comments/benchmark.json` — returns `2`.
- [ ] **6.5** `jq '.metadata.skill_version' evals/pr-comments/benchmark.json` matches `metadata.version` in `skills/pr-comments/SKILL.md`.
- [ ] **6.6** `jq '.run_summary_by_model | keys' evals/pr-comments/benchmark.json` — contains both `"claude-sonnet-4-6"` and `"claude-opus-4-7"`.
- [ ] **6.7** `jq '.run_summary.pass_rate.with_skill.mean == .run_summary_by_model["claude-opus-4-7"].pass_rate.with_skill.mean' evals/pr-comments/benchmark.json` — returns `true` (top-level mirrors latest model).
- [ ] **6.8** Spot-check one eval's Per-Eval Results row in `benchmark.md` against `jq '.runs[] | select(.eval_id == N and .executor_model == "claude-opus-4-7")'` output — values must match.
- [ ] **6.9** README `Eval Δ` per-model values match `run_summary_by_model[<model>].delta.pass_rate` (rounded to nearest whole percent).
- [ ] **6.10** `benchmark.md` "Models tested" header includes Opus 4.7 with the run date.
- [ ] **6.11** `benchmark.md` Summary-table `±` values match `run_summary_by_model` exactly (visual spot-check).
- [ ] **6.12** `uv run --with pytest pytest tests/` — no regressions.
- [ ] **6.13** `npx cspell README.md evals/pr-comments/benchmark.md specs/26-pr-comments-dual-model-benchmark/*.md` — clean; add new words to `cspell.config.yaml` in sorted position if needed.

---

## Phase 7: Peer review

*Fresh-context consistency pass before ship, to catch cross-file drift Phase 6's mechanical checks miss (stale deltas, Summary ± mismatches, `benchmark.md` vs `benchmark.json` drift, README deltas vs `run_summary_by_model`, plan.md ↔ tasks.md gaps). Exit condition: a pass produces zero valid findings. Iteration cap: 4.*

- [ ] **7.1** Stage all spec-26 changes in the worktree.
- [ ] **7.2** Run `/peer-review` (or `/peer-review --model <tool>`) and apply valid findings. Loop until zero valid findings or iteration cap 4. Record per-iteration summary inline in this task.

---

## Phase 8: Ship

- [ ] **8.1** Commit all changes on branch `evals/pr-comments-opus-4-7-multi-model`.
- [ ] **8.2** Push and open PR; run `/pr-comments {pr_number}` immediately per CLAUDE.md post-push convention.
- [ ] **8.3** Loop `/pr-comments` until no new bot feedback.
- [ ] **8.4** Run `/pr-human-guide` to annotate the PR for human reviewers (per CLAUDE.md pre-merge rule).
- [ ] **8.5** Wait for human review. After approval: squash-merge via `gh pr merge --squash --delete-branch`, sync local main, remove the worktree directory.
