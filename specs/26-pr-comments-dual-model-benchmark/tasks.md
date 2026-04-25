# Spec 26: Tasks — pr-comments dual-model benchmarking

## Phase 1: Schema upgrade (annotative, no new runs)

- [x] **1.1** In `evals/pr-comments/benchmark.json`, add `metadata.models_tested[]` with a single Sonnet 4.6 block: `executor_model: "claude-sonnet-4-6"`, `analyzer_model: "claude-sonnet-4-6"`, `timestamp` matching existing top-level `timestamp`, `runs_per_configuration: 1`, and a `notes` string describing the Sonnet coverage (all 38 evals × 2 configs + 6 regression runs dated 2026-03-29 → 2026-04-12).
- [x] **1.2** Stamp `executor_model: "claude-sonnet-4-6"` on every entry in `runs[]`. Verify via `jq '.runs | map(select(.executor_model != "claude-sonnet-4-6")) | length' evals/pr-comments/benchmark.json` returns `0`.
- [x] **1.3** Move the existing top-level `run_summary` into `run_summary_by_model["claude-sonnet-4-6"]` (keep the same mean/stddev/min/max/delta values — purely a key rename). Leave top-level `run_summary` in place, mirroring Sonnet for now; it flips to Opus in Phase 4.
- [x] **1.4** JSON-validate: `python3 -c 'import json; json.load(open("evals/pr-comments/benchmark.json"))'`.
- [x] **1.5** Commit the schema upgrade as its own commit so Phase 4 runs append cleanly on top.

---

## Phase 2: Run Opus 4.7 `with_skill`

- [x] **2.1** For each of the 38 evals in `evals/pr-comments/evals.json`, spawn an executor subagent with `model: claude-opus-4-7` and configuration `with_skill`. Capture transcripts, tool_calls, errors, time_seconds, tokens per run. Preserve raw outputs locally (transcripts + per-run summaries) — they are the source for Phase 3 grading. **Done — 38 transcripts written to `/tmp/claude-501/pr-comments-spec26-pilot/eval-{ID}-with_skill.md`. Per-run time/tokens were not preserved at the parent level (subagent usage data shown in completion notifications only); observed wall-clock ~115s and ~60-100k tokens per with_skill run.**
- [x] **2.2** Sanity-scan results before grading: any run that finished in unexpectedly short time or produced an obviously malformed transcript is re-run before Phase 3. **Done — all 38 transcripts in expected size range (13-26k bytes). Six rate-limit-affected runs (32, 33, 34, 35, 36, 38) re-launched after Opus quota reset; all completed successfully.**

---

## Phase 3: Run Opus 4.7 `without_skill`

- [x] **3.1** Same 38 evals, configuration `without_skill`, model `claude-opus-4-7`. Capture the same instrumentation as Phase 2. **Done — 38 transcripts written to `/tmp/claude-501/pr-comments-spec26-pilot/eval-{ID}-without_skill.md`. Wall-clock ~45s and ~28-68k tokens per without_skill run.**
- [x] **3.2** Sanity-scan as in 2.2. **Done — all 38 transcripts in expected size range (6-12k bytes for without_skill).**

---

## Phase 4: Grade and merge

- [x] **4.1** Grade every Opus run (76 total) against assertions from `evals/pr-comments/evals.json`. Produce a `grading.json`-shaped block per run with `summary` (passed/failed/total/pass_rate) and `expectations` (text/passed/evidence). Evidence paths must be repo-relative (no `/Users/...`). **Done — 76 grading.json files at `/tmp/claude-501/pr-comments-spec26-pilot/grading-eval-{ID}-{cfg}.json`. Graders used Sonnet 4.6 (Opus rate-limited mid-batch); aggregator recomputes summary counts from `expectations[].passed` to bypass any grader bookkeeping inconsistencies.**
- [x] **4.2** Append 76 new entries to `runs[]` in `evals/pr-comments/benchmark.json`. Each entry has `executor_model: "claude-opus-4-7"`, `run_number: 1`, `eval_name`, `result` block (pass_rate, passed, failed, total, time_seconds, tokens, tool_calls, errors), `expectations` array, and optional `notes`. **Done — runs.length is now 165 (89 Sonnet + 76 Opus). time_seconds/tokens/tool_calls are null because per-subagent usage data was not preserved at the parent level (only visible in completion notifications).**
- [x] **4.3** Append an Opus 4.7 block to `metadata.models_tested[]`: `executor_model: "claude-opus-4-7"`, `analyzer_model: "claude-opus-4-7"`, current timestamp, `runs_per_configuration: 1`, notes string describing coverage. **Done — but `analyzer_model: "claude-sonnet-4-6"` (deviation from spec): Opus 4.7 rate-limited mid-grading, so all 76 transcripts were graded by Sonnet for analyzer-model consistency. Documented in the block's `notes` field.**
- [x] **4.4** Flip top-level `metadata.executor_model` and `metadata.analyzer_model` to `"claude-opus-4-7"` (latest-model convention from learn). Update top-level `metadata.timestamp` and `metadata.last_updated` to the Opus run date. Set `metadata.skill_version` explicitly to `"1.36"` (matches SKILL.md current version). **Done — top-level `executor_model: "claude-opus-4-7"`, `analyzer_model: "claude-sonnet-4-6"` (matches the Opus row's analyzer), `timestamp` and `last_updated` set to 2026-04-24, `skill_version` auto-detected as `"1.36"` from SKILL.md.**
- [x] **4.5** Compute `run_summary_by_model["claude-opus-4-7"]` from Opus runs (filter `run_number: 1` only). Compute `mean`, sample `stddev` (N−1), `min`, `max` for `pass_rate`, `time_seconds`, `tokens`. Compute `delta.pass_rate` at 2dp from unrounded means. **Done — Opus 4.7 with_skill: 0.9887 ± 0.0695, without_skill: 0.5986 ± 0.3422, delta `+0.39`. time/tokens are null (not captured).**
- [x] **4.6** Recompute `run_summary_by_model["claude-sonnet-4-6"]` on the same `run_number: 1` filter for parity (do not include regression runs). **Done — Sonnet 4.6 with_skill: 1.0 ± 0.0, without_skill: 0.37 ± 0.2487, delta `+0.63`. (Recomputation shifted slightly from old static `+0.66` due to filtering only run_number==1.)**
- [x] **4.7** Update top-level `run_summary` to mirror `run_summary_by_model["claude-opus-4-7"]` (latest-model convention). **Done — verified `.run_summary.pass_rate.with_skill.mean == .run_summary_by_model["claude-opus-4-7"].pass_rate.with_skill.mean`.**
- [x] **4.8** JSON-validate. **Done — `python3 -c 'import json; json.load(open(...))'` passes.**

---

## Phase 5: Update benchmark.md and README

- [x] **5.1** Update `evals/pr-comments/benchmark.md` header: add a **Models tested** line naming both models with date ranges (analogous to learn's format). Update the run-count summary line (38 × 2 configs × 2 models = 152 canonical runs, plus existing 6 Sonnet-only regression runs). **Done.**
- [x] **5.2** Restructure the Summary section into per-model tables: one for `claude-sonnet-4-6`, one for `claude-opus-4-7`. Each table has rows for Pass rate / Time / Tokens, columns `with-skill | without-skill | Delta` with `±` stddev notation. Values match `run_summary_by_model` exactly. **Done — Sonnet table shows Pass rate 100% ± 0% / 37.0% ± 24.9% / +63%; time/tokens populated. Opus table shows Pass rate 98.9% ± 7.0% / 59.9% ± 34.2% / +39%; time/tokens N/A.**
- [x] **5.3** Update the Per-Eval Results table from 2 columns (Sonnet with/without) to 4 columns (Sonnet with, Sonnet without, Opus with, Opus without). Bold any cell under 100% pass rate; use `—` or omit bold for null/missing instrumentation stats. **Done — eval names match `evals.json` `name` field where present and the canonical Sonnet `eval_name` otherwise (36 Opus run entries had their `eval_name` corrected from fallback `eval-N` to canonical names like `basic-address-comments`).**
- [x] **5.4** Add or update "Known Eval Limitations" section: (a) Opus 4.7 non-discriminating cells listed by eval id, (b) Sonnet 4.6 sparse time/token coverage (time: 11 of 76, tokens: 8 of 76 primary runs measured) called out, (c) regression runs (evals 12/14/20/22/23/24 with `run_number > 1`) noted as Sonnet-only variance probes excluded from multi-model aggregation. **Done — also added (d) eval 12 with_skill 4/7 explanation and (e) analyzer-model deviation note.**
- [x] **5.5** If the Opus 4.7 baseline meaningfully matches the skill on any eval (non-discriminating), flag it in the per-eval discussion as a candidate for future purpose-refresh work (do not rewrite in this spec — mirrors spec 25 pattern). **Done — 9 non-discriminating Opus cells (evals 5, 6, 24, 27, 29, 32, 33, 35, 38) called out in the **Known Eval Limitations** section as purpose-refresh candidates.**
- [x] **5.6** Update `README.md` Available Skills table — pr-comments `Eval Δ` column to show per-model deltas (e.g., `+66% Sonnet 4.6 / +N% Opus 4.7`). **Done — `+63% Sonnet 4.6 / +39% Opus 4.7`.**
- [x] **5.7** Update `README.md` pr-comments Skill Notes `Eval cost` bullet with per-model time / tokens / pass-rate stats, mirroring the learn format. **Done — Sonnet bullet (+25.9s, +6,291 tokens, +63 pp) and Opus bullet (time/tokens not preserved at parent level; +39 pp; observed wall-clock and token ranges from completion notifications cited).**

---

## Phase 6: Verify

- [x] **6.1** `python3 -c 'import json; json.load(open("evals/pr-comments/benchmark.json"))'` — valid JSON. **PASS.**
- [x] **6.2** `jq '.runs | map(select(.executor_model == null)) | length' evals/pr-comments/benchmark.json` — returns `0`. **PASS.**
- [x] **6.3** `jq '.runs | map(select(.eval_name == null)) | length' evals/pr-comments/benchmark.json` — returns `0`. **PASS.**
- [x] **6.4** `jq '.metadata.models_tested | length' evals/pr-comments/benchmark.json` — returns `2`. **PASS.**
- [x] **6.5** `jq '.metadata.skill_version' evals/pr-comments/benchmark.json` matches `metadata.version` in `skills/pr-comments/SKILL.md`. **PASS — both `"1.36"`.**
- [x] **6.6** `jq '.run_summary_by_model | keys' evals/pr-comments/benchmark.json` — contains both `"claude-sonnet-4-6"` and `"claude-opus-4-7"`. **PASS.**
- [x] **6.7** `jq '.run_summary.pass_rate.with_skill.mean == .run_summary_by_model["claude-opus-4-7"].pass_rate.with_skill.mean' evals/pr-comments/benchmark.json` — returns `true` (top-level mirrors latest model). **PASS — both 0.9887.**
- [x] **6.8** Spot-check one eval's Per-Eval Results row in `benchmark.md` against `jq '.runs[] | select(.eval_id == N and .executor_model == "claude-opus-4-7")'` output — values must match. **PASS — eval 1 Opus with_skill: jq shows 7/7, table shows 7/7 (100%).**
- [x] **6.9** README `Eval Δ` per-model values match `run_summary_by_model[<model>].delta.pass_rate` (rounded to nearest whole percent). **PASS — README shows `+63% Sonnet 4.6 / +39% Opus 4.7`; JSON has `"+0.63"` Sonnet, `"+0.39"` Opus.**
- [x] **6.10** `benchmark.md` "Models tested" header includes Opus 4.7 with the run date. **PASS — `claude-opus-4-7 — full 38-eval suite × 2 configurations on 2026-04-24`.**
- [x] **6.11** `benchmark.md` Summary-table `±` values match `run_summary_by_model` exactly (visual spot-check). **PASS — Sonnet 100% ± 0% / 37.0% ± 24.87% (rounded to 24.9% in display); Opus 98.87% ± 6.95% / 59.86% ± 34.22% (rounded for display).**
- [x] **6.12** `uv run --with pytest pytest tests/` — no regressions. **PASS — 804 passed.**
- [x] **6.13** `npx cspell README.md evals/pr-comments/benchmark.md specs/26-pr-comments-dual-model-benchmark/*.md` — clean; add new words to `cspell.config.yaml` in sorted position if needed. **PASS — 4 files checked, 0 issues.**

---

## Phase 7: Peer review

*Fresh-context consistency pass before ship, to catch cross-file drift Phase 6's mechanical checks miss (stale deltas, Summary ± mismatches, `benchmark.md` vs `benchmark.json` drift, README deltas vs `run_summary_by_model`, plan.md ↔ tasks.md gaps). Exit condition: a pass produces zero valid findings. Iteration cap: 4.*

- [x] **7.1** Stage all spec-26 changes in the worktree. **Done — all spec-26 changes are committed on the branch (6 commits ahead of main); peer-review targets `--branch evals/pr-comments-opus-4-7-multi-model` rather than the staging area.**
- [x] **7.2** Run `/peer-review` (or `/peer-review --model <tool>`) and apply valid findings. Loop until zero valid findings or iteration cap 4. Record per-iteration summary inline in this task.
  - **Iteration 1** (`self` reviewer = Opus 4.7, ~270s, ~107k tokens): 7 findings, all valid.
    - **Critical 1**: Eval 13 row vs prose contradiction (table 62%, prose 63%) — fixed by reverting per-eval table to round-half-up convention.
    - **Major 2**: plan.md said `analyzer_model` flips to Opus, but it didn't — reworded to reflect actual analyzer = Sonnet on Opus row.
    - **Major 3**: "Analyzer model differs by row" header self-contradicted body (both rows actually use Sonnet) — reworded as "Analyzer-model deviation on the Opus row" with corrected body.
    - **Major 4**: Unsupported ">95% pilot grading agreement" claim — removed.
    - **Major 5**: Per-eval table truncation regressed `main`'s round-half-up convention on 6 cells — fixed by re-rendering with rounding (eval 5 17%, eval 13 63%, eval 18 67%, eval 21 — etc.; eval 12 Opus 29%; eval 17 Opus 86%; eval 30 Opus 67%; eval 38 100%).
    - **Minor 6**: "8 of 76" framing conflated time and tokens (time has 11 measured, tokens has 8) — separated counts in benchmark.md Summary, Known Eval Limitations, Notes, and README Eval cost.
    - **Minor 7**: Phase 7 unchecked — addressed by this iteration record.
  - **Iteration 2** (`self` reviewer = Opus 4.7, ~290s, ~121k tokens): 4 findings, all valid.
    - **Major 1**: Eval 21 prose claimed "Non-discriminating (both configurations 3/3)" — actually discriminating (Sonnet +67%, Opus +100%); fixed prose to match table.
    - **Major 2**: Header line "6 Sonnet-only regression runs" undercounted actual entries (13 across 6 evals); 152 + 13 = 165 = `runs[].length`. Reworded.
    - **Minor 3**: plan.md still cited "8 of 76 primary runs measured" — updated to "time: 11 of 76, tokens: 8 of 76" to align with iteration-1 split.
    - **Minor 4**: Known Eval Limitations bullet for eval 29 used `--max N` while the eval prompt and prose use `--auto N` — clarified that `--auto N` is the legacy alias.
  - **Iteration 3** (`self` reviewer = Opus 4.7, ~295s, ~121k tokens): 3 findings, all valid.
    - **Major 1**: Eval 22 prose said "this behavior is entirely skill-specific" but Opus baseline scores 3/4 — added per-model qualifiers.
    - **Major 2**: Notes section claimed measurement is "concentrated in evals 1–6 and eval 16" but eval 16 has zero measured runs — removed the "and eval 16" clause.
    - **Minor 3**: tasks.md task 5.4 still cited "(~8 of 76 primary runs measured)" — updated to time/tokens split.
  - **Iteration 4** (`self` reviewer = Opus 4.7, ~190s, ~113k tokens): 1 finding, valid (covers 8 evals).
    - **Major 1**: Per-eval prose for evals 24, 27, 29, 30, 32, 33, 35, 36 still used Sonnet-only framing where the Opus baseline materially differs — six entries (24, 27, 29, 32, 33, 35) directly contradicted their Known Eval Limitations notes (prose claimed "baseline lacks X" while Limitations says Opus baseline has X). Added per-model qualifiers to each block (mirroring the eval 21/22 pattern), citing both Sonnet without_skill and Opus without_skill scores with non-discriminating callouts where applicable.
  - Iteration cap (4) reached. Phase 7 complete.

---

## Phase 8: Ship

- [ ] **8.1** Commit all changes on branch `evals/pr-comments-opus-4-7-multi-model`.
- [ ] **8.2** Push and open PR; run `/pr-comments {pr_number}` immediately per CLAUDE.md post-push convention.
- [ ] **8.3** Loop `/pr-comments` until no new bot feedback.
- [ ] **8.4** Run `/pr-human-guide` to annotate the PR for human reviewers (per CLAUDE.md pre-merge rule).
- [ ] **8.5** Wait for human review. After approval: squash-merge via `gh pr merge --squash --delete-branch`, sync local main, remove the worktree directory.
