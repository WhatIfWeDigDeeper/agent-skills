# Spec 25: Tasks — learn purpose refresh

## Phase 1: Draft new evals

- [ ] **1.1** Add eval 5 (noise rejection) to `evals/learn/evals.json` with full assertion set — see plan.md "Eval 5" section for prompt shape and discriminating assertion
- [ ] **1.2** Add eval 6 (environment-scope labeling) to `evals/learn/evals.json`
- [ ] **1.3** Add eval 7 (cross-assistant-sync rule) to `evals/learn/evals.json` — fixture must include both CLAUDE.md (with sync rule text) and `.github/copilot-instructions.md`
- [ ] **1.4** Add eval 8 (silent contradiction) to `evals/learn/evals.json` — fixture CLAUDE.md must contain a rule the new learning will contradict
- [ ] **1.5** Review all four eval prompts for skill-name leakage (no phrases like "invoke the learn skill") per `evals/CLAUDE.md`

---

## Phase 2: Baseline-validate discrimination (before changing skill)

- [ ] **2.1** Run evals 5–8 with `without_skill` on `claude-opus-4-7`; record raw results **and preserve the run outputs** — these become the final benchmark `without_skill` entries for the kept evals in task 4.5. Do not re-run in Phase 4; reusing these runs avoids drift between the Phase 2 discrimination gate and the published benchmark.
- [ ] **2.2** For each new eval, confirm at least one assertion fails without_skill on Opus 4.7. If an eval passes fully, revise the prompt once (bury signal deeper, subtle contradiction) and retry. If the revised eval still doesn't discriminate, **drop it from the suite** — a non-discriminating eval is a non-signal eval. Record the final kept eval ID set here before Phase 3 starts, and let **K = the count of kept evals** (K ∈ {1..4}); all downstream counts (evals_run, token-denominator, Summary table rows, README delta) derive from K and the kept ID set. If K = 0 (every new eval dropped), the spec aborts — no discriminating signal means no purpose refresh.
- [ ] **2.3** Also run evals 5–8 `without_skill` on `claude-sonnet-4-6` to establish that-model baseline (no discrimination gate — just collect data); preserve outputs — these also become final benchmark `without_skill` entries for the kept evals in task 4.5.

*Gate: do not move to Phase 3 until 2.2 concludes — either every kept eval discriminates, or the non-discriminating one has been dropped with rationale recorded in the task item.*

---

## Phase 3: Rewrite SKILL.md

- [ ] **3.1** In `skills/learn/SKILL.md`, restructure Step 2 so the "ask yourself" questions lead the step and the scan list follows as what-to-look-for given those filters
- [ ] **3.2** Add new Step 4 "Preserve Cross-Config Sync Rules" between current Step 3 (Route) and current Step 4 (Plan); renumber downstream steps. **Scope to Markdown-based configs only** (`CLAUDE.md`, `GEMINI.md`, `AGENTS.md`, `.github/copilot-instructions.md`); explicitly note that `.cursor/rules/*.mdc` and `.continuerc.json` are out of scope — mirror-rule detection in those formats is deferred. Per the plan sketch (`## New evals` → Eval 7, and `## Skill changes` → "What the new cross-sync step looks like" block), within the Markdown scope the step must: (a) detect mirror-rule text in each config that references the others (patterns like "keep X in sync", "mirror … to"), (b) respect the user's disambiguation choice from Step 1 — operate only on configs the user chose to update; mirror-rules in an unchosen config do **not** trigger fan-out, (c) preserve the mirror-rule text during edits — do not clobber it during a section rewrite, and (d) add a reciprocal mirror-rule to any chosen config that lacks one naming the other chosen configs. Optionally augment the Step 1 disambiguation prompt to surface detected mirror-rules as informational context, but the prompt does not coerce the user's choice. Include a "Why" clause explaining that the mirror-rule is load-bearing for future sessions, and that user choice still binds because legitimate reasons may exist to scope a learning narrowly.
- [ ] **3.3** In the Plan step (Step 5 after 3.2 inserts the cross-sync step; was Step 4), add a pre-present audit sub-step: before showing each drafted entry to the user, apply the `## Principles` "Minimum viable rule text" check ("is this the min chars necessary?") to every clause and cut what can't be defended. Principles are passive until a numbered step invokes them — the workflow must run the audit explicitly rather than relying on the agent to self-apply a guideline.
- [ ] **3.4** Replace the `## NEVER` and `## Guidelines` blocks with a single `## Principles` section per plan.md sketch — target 5 principles, each leading with the rule and explaining why
- [ ] **3.5** Verify the Sonnet 4.6 eval 2 sentinel behavior is still explicit in the rewritten skill (multi-target routing + plan-before-apply) — not lost in the consolidation
- [ ] **3.6** Bump `metadata.version` from `"0.9"` to `"1.0"` in the same edit
- [ ] **3.7** `wc -l skills/learn/SKILL.md` — record both the pre-rewrite and post-rewrite line counts; target is no substantial growth (post-rewrite within ±10% of pre-rewrite) after adding the cross-sync step and consolidating principles.

---

## Phase 4: Run full benchmark

Phase 4 produces runs in two groups on both models: (a) `with_skill` for each kept new eval (4.1, 4.2), and (b) v1.0 `with_skill` re-runs of evals 0–4 that replace the superseded v0.9 entries (4.3). `without_skill` runs for the kept new evals **are reused from Phase 2** (tasks 2.1, 2.3) — do not re-run them; reusing avoids drift between the Phase 2 discrimination gate and the published benchmark. `without_skill` runs for evals 0–4 carry over from the existing `benchmark.json`. Tasks are numbered in execution order — grading (4.4) follows all run-producing tasks.

- [ ] **4.1** Run `with_skill` × `claude-opus-4-7` for the kept evals recorded in 2.2 (K runs on Opus)
- [ ] **4.2** Run `with_skill` × `claude-sonnet-4-6` for the kept evals recorded in 2.2 (K runs on Sonnet)
- [ ] **4.3** Re-run evals 0–4 `with_skill` on both models (`claude-opus-4-7` and `claude-sonnet-4-6`) at skill version 1.0 — these will replace the superseded v0.9 `with_skill` run entries in `benchmark.json` during 4.5. Without_skill runs for evals 0–4 carry over (they don't depend on skill version). Verify the Sonnet 4.6 eval 2 sentinel (+40 pp lift on that cell) is preserved; if not, return to Phase 3 and investigate before moving on. Also serves as a regression check on the rewrite — evals 3 and 4 should still land 6/6 with_skill.
- [ ] **4.4** Grade every run produced in 4.1, 4.2, and 4.3, plus the Phase 2 `without_skill` runs from 2.1 and 2.3 for the kept evals (if they were not already graded at the gate); capture `time_seconds`, `tokens`, `tool_calls`, `errors` per `evals/CLAUDE.md`
- [ ] **4.5** Append new-eval run entries to `evals/learn/benchmark.json` — both the `with_skill` entries from 4.1/4.2 and the `without_skill` entries reused from Phase 2 runs (2.1, 2.3) for each kept eval; replace the superseded v0.9 `with_skill` entries for evals 0–4 with the 4.3 re-runs. Set `eval_name` on every entry — use kebab-case descriptive slugs (eval 5 → `noise-rejection`, 6 → `environment-scope-labeling`, 7 → `cross-assistant-sync`, 8 → `silent-contradiction`); preserve existing `eval_name` values on 0–4 re-runs.
- [ ] **4.6** Update `metadata.evals_run` to `[0,1,2,3,4]` plus the kept subset recorded in 2.2 (e.g. `[0,1,2,3,4,5,6,7,8]` when K = 4); set `metadata.skill_version` to `"1.0"`
- [ ] **4.7** Recompute `run_summary` and `run_summary_by_model` from the full run set (sample stddev, unrounded means for deltas); delta `pass_rate` at 2-decimal precision

---

## Phase 5: Update benchmark.md and README

- [ ] **5.1** Update `benchmark.md` **Models tested** header line — add the v1.0 re-run dates for both `claude-sonnet-4-6` and `claude-opus-4-7` alongside the existing v0.9 dates; keep the dates for `without_skill` runs that carry over
- [ ] **5.2** Update `benchmark.md` **Evals** total-count line — new shape: `(5 + K) × 2 configurations × 2 models = 4·(5+K) runs total` (or equivalent). Total reflects the final retained run set only; v1.0 `with_skill` re-runs of evals 0–4 replace the superseded v0.9 entries, they do not append.
- [ ] **5.3** Update `benchmark.md` `## Per-Eval Results` table — add a row per kept eval in 5–8, and update the existing rows for 0–4 with their v1.0 `with_skill` pass counts
- [ ] **5.4** Add per-eval sections to `evals/learn/benchmark.md` for each kept eval in 5–8 (prompt summary, what it tests, per-configuration pass rates)
- [ ] **5.5** Update `benchmark.md` Summary tables (per-model) with new means, stddevs, and deltas; Summary-table `±` values must match `run_summary` / `run_summary_by_model`
- [ ] **5.6** Reconcile `benchmark.md`'s token-denominator note with the final run set. If all runs in the final set have token stats captured (uniform population), no sentence is needed. If partial (e.g., some re-runs lack tokens), add or update the `Token statistics are computed only over N of M primary runs per configuration` sentence with M = 5 + K per model and N = runs with token stats. For the combined-across-models denominator used elsewhere in `benchmark.md`, use 10 + 2K. The sentence does not currently exist in benchmark.md, so this may be an *add* rather than an *update*.
- [ ] **5.7** Update `benchmark.md` "Known Eval Limitations" — replace the "19 of 20 cells non-discriminating" framing with the new discrimination picture. Summarize which evals discriminate on which models after v1.0, referencing the K kept evals and noting whether any baseline evals 0–4 changed discrimination status at v1.0.
- [ ] **5.8** Update `README.md` Available Skills table — `Eval Δ` column for learn
- [ ] **5.9** Update `README.md` learn Skill Notes — `Eval cost` bullet (+X seconds, +N tokens over baseline; discriminating eval count)

---

## Phase 6: Verify

- [ ] **6.1** `rg "NEVER" skills/learn/SKILL.md` — confirm consolidation landed (expect sharp reduction, not zero; a hard prohibition may still earn NEVER)
- [ ] **6.2** `metadata.version: "1.0"` in `SKILL.md` frontmatter
- [ ] **6.3** `metadata.skill_version: "1.0"` in `benchmark.json`
- [ ] **6.4** Every `runs[*]` entry in `benchmark.json` has `eval_name` populated
- [ ] **6.5** `uv run --with pytest pytest tests/` — no regressions
- [ ] **6.6** `npx cspell README.md skills/learn/SKILL.md evals/learn/benchmark.md specs/25-learn-purpose-refresh/*.md` — clean. If task 3.2(d) added a reciprocal mirror-rule to `.github/copilot-instructions.md`, include that file in the sweep too. (Add any new words to `cspell.config.yaml`.)
- [ ] **6.7** `python3 -c 'import json; json.load(open("evals/learn/benchmark.json"))'` — valid JSON
- [ ] **6.8** README.md `Eval Δ` for learn matches per-model deltas from `run_summary_by_model[<model>].delta.pass_rate` (rounded) — the README shows per-model values; `run_summary.delta.pass_rate` at top level mirrors only the latest model and is not the source for the README
- [ ] **6.9** `benchmark.md` Summary-table `±` values match `run_summary` / `run_summary_by_model` exactly
- [ ] **6.10** `benchmark.md` `**Models tested**` header includes v1.0 re-run dates for both models
- [ ] **6.11** `benchmark.md` `**Evals**` total-count line reflects 5 + K evals and 4·(5+K) runs total
- [ ] **6.12** `benchmark.md` `## Per-Eval Results` table has a row for every kept eval in 5–8 and updated v1.0 rows for evals 0–4
- [ ] **6.13** `benchmark.md` `## Known Eval Limitations` no longer uses the 19-of-20 non-discriminating framing
- [ ] **6.14** Confirm v0.9 `with_skill` rows for evals 0–4 were fully replaced. Run entries in `benchmark.json` do not carry per-run `skill_version` in the current schema, so the mechanical check is count-based: `jq '[.runs[] | select(.configuration=="with_skill")] | sort_by(.eval_id) | group_by(.eval_id) | map({eval_id: .[0].eval_id, count: length})' evals/learn/benchmark.json` — expect each eval_id in the final set to have exactly 2 `with_skill` entries (one per model). Combined with task 4.3 + 4.5 execution discipline, this confirms no v0.9 `with_skill` rows survived.
- [ ] **6.15** `metadata.evals_run` in `benchmark.json` matches `[0,1,2,3,4]` plus the kept subset recorded in task 2.2

---

## Phase 7: Ship

- [ ] **7.1** Commit on branch `evals/learn-purpose-refresh`
- [ ] **7.2** Push, open PR; run `/pr-comments` immediately after PR creation per project convention
- [ ] **7.3** Address review comments; squash-merge, delete branch, sync local main
