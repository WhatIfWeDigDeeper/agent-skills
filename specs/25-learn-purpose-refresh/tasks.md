# Spec 25: Tasks — learn purpose refresh

## Phase 1: Draft new evals

- [x] **1.1** Add eval 5 (noise rejection) to `evals/learn/evals.json` with full assertion set — see plan.md "Eval 5" section for prompt shape and discriminating assertion
- [x] **1.2** Draft eval 6 (environment-scope labeling) for `evals/learn/evals.json`, then drop it at the Phase 2 discrimination gate
- [x] **1.3** Add eval 7 (cross-assistant-sync rule) to `evals/learn/evals.json` — fixture must include both CLAUDE.md (with sync rule text) and `.github/copilot-instructions.md`
- [x] **1.4** Add eval 8 (silent contradiction) to `evals/learn/evals.json` — fixture CLAUDE.md must contain a rule the new learning will contradict
- [x] **1.5** Resolve eval 9 harness pattern. Existing `evals.json` schema has a single `prompt` string per eval; eval 9 needs a follow-up turn. Option (b) from plan.md — embedding the follow-up inside the initial prompt — is rejected upfront because it contaminates the first draft. Decide between the remaining options: (a) extend the runner to support a `followup_prompt` field and a two-turn transcript, or (c) fall back to a single-turn threshold assertion ("rule text ≤ 2 sentences AND ≤ 200 chars"). Record the decision here before 1.6. **Decision: option (a).** The evals in this repo are executed by subagents reading `evals.json`, not a formal typed runner — adding an optional `followup_prompt` field is a documentation change (executor subagent is told: if present, issue a second turn after the first draft). This preserves the primary signal (did the audit fire unprompted on turn 1) that option (c) dilutes.
- [x] **1.6** Add eval 9 (min-char audit) to `evals/learn/evals.json` using the pattern decided in 1.5. Prompt invites verbose rule text (incident narrative, multi-clause consequences, or explanatory rationale the agent is tempted to narrate in the rule body). Assertion per plan.md "Eval 9" section (primary signal: turn-1 ≤ 200 chars; corroboration: turn-2 affirmation regex or bounded rewrite — see plan.md for the full rule).
- [x] **1.7** Review all five eval prompts for skill-name leakage (no phrases like "invoke the learn skill") per `evals/CLAUDE.md`

---

## Phase 2: Baseline-validate discrimination (before changing skill)

- [x] **2.1** Run evals 5–9 with `without_skill` on `claude-opus-4-7`; record raw results **and preserve the run outputs** — these become the final benchmark `without_skill` entries for the kept evals in task 4.5. Do not re-run in Phase 4; reusing these runs avoids drift between the Phase 2 discrimination gate and the published benchmark. **Run outputs were preserved locally (modified files, summaries, tool_calls, tokens).**
- [x] **2.2** **Kept (K = 4): evals 5, 7, 8, 9.** Dropped: eval 6 (environment-scope-labeling) — Opus 4.7 and Sonnet 4.6 baselines both scored 5/5 without_skill; both naturally scoped the `--no-gpg-sign` fix with conditional phrasing ("when the keyring is borked") and preserved the existing branch-protection rule. Revising the prompt to strip scope context would either make it ambiguous (baseline has to guess scope) or overlap with eval 8's contradiction-detection signal (universal framing contradicts the branch-protection rule already in the file), so the single-revision gate exits with a drop rather than a duplicative test. **Kept discrimination picture on Opus 4.7 without_skill:** eval 5 → 4/5 (failed rejects-npm-install-noise), eval 7 → 4/5 (failed reciprocal-sync-rule-added), eval 8 → 4/5 (failed summary-names-contradiction), eval 9 → 2/5 (failed turn1-rule-under-200-chars, turn2-affirmation-or-bounded-rewrite, no-incident-narrative-in-rule).
- [x] **2.3** Also run evals 5–9 `without_skill` on `claude-sonnet-4-6` to establish that-model baseline (no discrimination gate — just collect data); preserve outputs — these also become final benchmark `without_skill` entries for the kept evals in task 4.5. **Sonnet 4.6 baselines were preserved locally with the Phase 2 run outputs. On kept evals without_skill Sonnet 4.6:** eval 5 → 1/5, eval 7 → 4/5, eval 8 → 4/5, eval 9 → 2/5.

*Gate: do not move to Phase 3 until 2.2 concludes — either every kept eval discriminates, or any non-discriminating evals have been dropped with rationale recorded per-eval in the task item.*

---

## Phase 3: Rewrite SKILL.md

- [x] **3.1** In `skills/learn/SKILL.md`, restructure Step 2 so the "ask yourself" questions lead the step and the scan list follows as what-to-look-for given those filters. **Done:** Step 2 now opens with "Default is **reject**. Each candidate learning must earn inclusion by passing three filters in order" followed by the three filters (Would I forget, Is this already covered, Universal or local), then the shape-scan list.
- [x] **3.2** Add new Step 4 "Preserve Cross-Config Sync Rules" between current Step 3 (Route) and current Step 4 (Plan); renumber downstream steps. **Done:** New Step 4 scopes to Markdown configs (CLAUDE.md, GEMINI.md, AGENTS.md, `.github/copilot-instructions.md`); explicitly excludes `.cursor/rules/*.mdc` and `.continuerc.json`; implements all four sub-behaviors (detect, respect Step 1 choice, preserve, reciprocate); includes "Why" clause. Step 1 multi-config prompt augmented with mirror-rule informational hint. Downstream steps renumbered (Plan → 5, Apply → 6, Summarize → 7).
- [x] **3.3** In the Plan step (Step 5 after 3.2 inserts the cross-sync step; was Step 4), add a pre-present audit sub-step: before showing each drafted entry to the user, apply the `## Principles` "Minimum viable rule text" check ("is this the min chars necessary?") to every clause and cut what can't be defended. Principles are passive until a numbered step invokes them — the workflow must run the audit explicitly rather than relying on the agent to self-apply a guideline. **Done:** Step 5 now opens with "Before showing the plan, **audit each drafted rule body against the Principles' 'Minimum viable rule text' check**" and explicitly calls out that the audit is not optional.
- [x] **3.4** Replace the `## NEVER` and `## Guidelines` blocks with a single `## Principles` section per plan.md sketch — target 5 principles, each leading with the rule and explaining why. **Done:** 5 principles (reject noise, annotate scope, one topic/one location, surface contradictions, min viable rule text). Kept a single NEVER prohibition for vague learnings (specificity is non-negotiable for every other principle).
- [x] **3.5** Verify the Sonnet 4.6 eval 2 sentinel behavior is still explicit in the rewritten skill (multi-target routing + plan-before-apply) — not lost in the consolidation. **Verified:** multi-target routing preserved in Step 1's "Multiple configs found → stop and ask" prompt with numbered choice + "all" option; plan-before-apply preserved as the last sentence of Step 5: "Do not modify any files until the user responds to this step."
- [x] **3.6** Bump `metadata.version` from `"0.9"` to `"1.0"` in the same edit. **Done.**
- [x] **3.7** `wc -l skills/learn/SKILL.md` — record both the pre-rewrite and post-rewrite line counts; target is no substantial growth (post-rewrite within ±10% of pre-rewrite) after adding the cross-sync step and consolidating principles. **Pre-rewrite: 150 lines. Post-rewrite: 161 lines. Delta: +7.3% — within ±10% target.**

---

## Phase 4: Run full benchmark

Phase 4 produces runs in two groups on both models: (a) `with_skill` for each kept new eval (4.1, 4.2), and (b) v1.0 `with_skill` re-runs of evals 0–4 that replace the superseded v0.9 entries (4.3). `without_skill` runs for the kept new evals **are reused from Phase 2** (tasks 2.1, 2.3) — do not re-run them; reusing avoids drift between the Phase 2 discrimination gate and the published benchmark. `without_skill` runs for evals 0–4 carry over from the existing `benchmark.json`. Tasks are numbered in execution order — grading (4.4) follows all run-producing tasks.

- [x] **4.1** Run `with_skill` × `claude-opus-4-7` for the kept evals recorded in 2.2 (K runs on Opus). **Done — all 4 runs pass 5/5 or 4/5 (eval 9 turn1-rule-under-200-chars is the one failing assertion).**
- [x] **4.2** Run `with_skill` × `claude-sonnet-4-6` for the kept evals recorded in 2.2 (K runs on Sonnet). **Done — same scores as Opus on Sonnet (5/5 across 5/7/8; 4/5 on 9).**
- [x] **4.3** Re-run evals 0–4 `with_skill` on both models at skill version 1.0. **Done** — all 10 re-runs score 5/5 or 6/6. Sonnet 4.6 eval 2 sentinel confirmed: with-skill 5/5 vs without-skill 3/5 → +40 pp on that cell preserved. Eval 3 (6/6) and eval 4 (6/6) regression check clean.
- [x] **4.4** Grade every run produced in 4.1, 4.2, 4.3, plus Phase 2 `without_skill` runs for kept evals. **Done — expectations populated per-run in benchmark.json; run logs preserved locally during the session.**
- [x] **4.5** Append new-eval run entries to `evals/learn/benchmark.json` — with_skill (4.1/4.2) + without_skill (Phase 2 reused); replace v0.9 with_skill entries for 0–4 with 4.3 re-runs. `eval_name` set on every entry. **Done via a local build script.** Final benchmark.json has 36 runs (9 evals × 2 configs × 2 models), every entry has `eval_name`.
- [x] **4.6** Updated `metadata.evals_run` → `[0,1,2,3,4,5,7,8,9]` (K=4); `metadata.skill_version` → `"1.0"`.
- [x] **4.7** Recomputed `run_summary` and `run_summary_by_model` from the full 36-run set. Sample stddev, deltas from unrounded means, `pass_rate` delta at 2dp. **Opus delta +0.11 / +7.5s / +10,083 tokens; Sonnet delta +0.22 / +23.0s / +10,154 tokens; top-level run_summary mirrors Opus per the existing convention.** (Sonnet stats reflect a re-run of eval 9 with_skill triggered by the PR-review tightening of the turn-2 affirmation assertion, per evals/CLAUDE.md "re-run don't re-grade".)

---

## Phase 5: Update benchmark.md and README

- [x] **5.1** Update `benchmark.md` **Models tested** header line. **Done** — added v1.0 re-run dates (2026-04-23) for both models; kept v0.9 without_skill dates for 0-4 carry-overs.
- [x] **5.2** Update `benchmark.md` **Evals** total-count line. **Done** — now reads "9 × 2 configurations × 2 models = 36 runs total" and notes eval 6 was drafted and dropped at the Phase 2 gate.
- [x] **5.3** Update `benchmark.md` `## Per-Eval Results` table. **Done** — added rows for 5, 7, 8, 9 (with discrimination cells bolded); evals 0-4 rows retained (pass counts unchanged at v1.0).
- [x] **5.4** Add per-eval sections for kept evals 5, 7, 8, 9. **Done** — each has prompt summary, what-it-tests, and per-configuration pass-rate discussion, including the eval 9 two-turn harness explanation and the turn-1 200-char false-negative note.
- [x] **5.5** Update Summary tables with new means, stddevs, deltas. **Done** — per-model tables refreshed to the final published values in `evals/learn/benchmark.md` / `README.md` (Sonnet 4.6: +22%; Opus 4.7: +11%). `±` values match `run_summary_by_model` exactly — verified by `python3 -c 'import json; print(json.dumps(json.load(open("evals/learn/benchmark.json"))["run_summary_by_model"], indent=2))'`.
- [x] **5.6** Reconcile token-denominator note. **Done (no sentence needed)** — all 36 runs have `tokens` populated in `benchmark.json`, so the `N of M` sentence from `evals/CLAUDE.md`'s rule does not apply; the prior benchmark.md did not have the sentence and it remains absent.
- [x] **5.7** Update "Known Eval Limitations". **Done** — replaced the "19 of 20 cells non-discriminating" framing with a per-model discrimination picture (5/9 on Sonnet, 4/9 on Opus). Documents the single v1.0 eval 9 false-negative (turn-1 rule body stays >200 chars on both models even with the audit) and the PR-review tightening of the turn-2 affirmation assertion (which triggered a Sonnet eval 9 re-run per the evals/CLAUDE.md re-run-don't-re-grade rule; re-run produced `already minimal` as the entire turn-2 response).
- [x] **5.8** Update `README.md` Available Skills table — Eval Δ column. **Done**: `+22% Sonnet 4.6 / +11% Opus 4.7`.
- [x] **5.9** Update `README.md` learn Skill Notes — Eval cost bullet. **Done**: bullet matches the final published benchmark values for Sonnet 4.6 (+23.0s / +10,154 tokens / +22% with 5 discriminating evals) and Opus 4.7 (+7.5s / +10,083 tokens / +11% with 4 discriminating evals).

---

## Phase 6: Verify

- [x] **6.1** `rg "NEVER" skills/learn/SKILL.md` — confirm consolidation landed (expect sharp reduction, not zero; a hard prohibition may still earn NEVER)
- [x] **6.2** `metadata.version: "1.0"` in `SKILL.md` frontmatter
- [x] **6.3** `metadata.skill_version: "1.0"` in `benchmark.json`
- [x] **6.4** Every `runs[*]` entry in `benchmark.json` has `eval_name` populated
- [x] **6.5** `uv run --with pytest pytest tests/` — no regressions
- [x] **6.6** `npx cspell README.md skills/learn/SKILL.md evals/learn/benchmark.md specs/25-learn-purpose-refresh/*.md` — clean. If task 3.2(d) added a reciprocal mirror-rule to `.github/copilot-instructions.md`, include that file in the sweep too. (Add any new words to `cspell.config.yaml`.)
- [x] **6.7** `python3 -c 'import json; json.load(open("evals/learn/benchmark.json"))'` — valid JSON
- [x] **6.8** README.md `Eval Δ` for learn matches per-model deltas from `run_summary_by_model[<model>].delta.pass_rate` (rounded) — the README shows per-model values; `run_summary.delta.pass_rate` at top level mirrors only the latest model and is not the source for the README
- [x] **6.9** `benchmark.md` Summary-table `±` values match `run_summary` / `run_summary_by_model` exactly
- [x] **6.10** `benchmark.md` `**Models tested**` header includes v1.0 re-run dates for both models
- [x] **6.11** `benchmark.md` `**Evals**` total-count line reflects 5 + K evals and 4·(5+K) runs total
- [x] **6.12** `benchmark.md` `## Per-Eval Results` table has a row for every kept eval in 5–9 and updated v1.0 rows for evals 0–4
- [x] **6.13** `benchmark.md` `## Known Eval Limitations` no longer uses the 19-of-20 non-discriminating framing
- [x] **6.14** Confirm v0.9 `with_skill` rows for evals 0–4 were fully replaced. Run entries in `benchmark.json` do not carry per-run `skill_version` in the current schema, so the mechanical check is count-based: `jq '[.runs[] | select(.configuration=="with_skill")] | sort_by(.eval_id) | group_by(.eval_id) | map({eval_id: .[0].eval_id, count: length})' evals/learn/benchmark.json` — expect each eval_id in the final set to have exactly 2 `with_skill` entries (one per model). Combined with task 4.3 + 4.5 execution discipline, this confirms no v0.9 `with_skill` rows survived.
- [x] **6.15** `metadata.evals_run` in `benchmark.json` matches `[0,1,2,3,4]` plus the kept subset recorded in task 2.2

---

## Phase 7: Peer Review

*Fresh-context consistency pass before ship, to catch cross-file drift Phase 6's mechanical checks miss (stale step references, Summary ± mismatches, `benchmark.md` vs `benchmark.json` drift, README deltas vs `run_summary_by_model`, plan.md ↔ tasks.md gaps, mirror-rule omissions). Exit condition: a pass produces zero valid findings. Iteration cap: 4.*

- [x] **7.1** Stage all spec-25 changes if not already staged. **Done**: 7 files staged (README.md, cspell.config.yaml, evals/learn/benchmark.json, evals/learn/benchmark.md, evals/learn/evals.json, skills/learn/SKILL.md, specs/25-learn-purpose-refresh/tasks.md).
- [x] **7.2** Loop completed in 2 iterations:
  - **Iteration 1** (`copilot:gpt-5.3-codex`, 2m 10s, 154.6k input / 6.9k output): 2 findings.
    - Major: "No automated test updates for substantial learn behavior changes" — **declined**. Rationale: spec 25 explicitly scopes test updates to evals (9 comprehensive evals added/updated); the learn skill's logic is prose-based with no classifiable unit-testable surface analogous to other skills' tests. Adding tests/learn/ would be scope creep per the spec's Risks section.
    - Minor: "`cspell` word list insertion appears out of sort order" — **applied**. Moved `duplicative` from between `dogfood`/`DOXYZ` to after `DOXYZ` (case-insensitive alphabetical: d-o-x < d-u). Re-staged `cspell.config.yaml`; cspell re-run clean.
  - **Iteration 2** (`copilot:gpt-5.3-codex`, 57s, 238.6k input / 2.9k output): NO FINDINGS. Loop exits on zero valid findings.
- [x] **7.3** 4-iteration cap not hit (exited at iteration 2). No unresolved items to record in PR description.

---

## Phase 8: Ship

- [x] **8.1** Commit on branch `evals/learn-purpose-refresh`
- [x] **8.2** Push, open PR; run `/pr-comments {pr_number}` immediately after PR creation
- [x] **8.3** Loop `/pr-comments` until no new bot feedback — **done in 6 iterations**. Iter 1 (2 findings, both applied). Iter 2 (5 findings: 3 applied, 2 declined Step 1/Step 4 mirror-rule-binding design decisions with rationale). Iter 3 (5 findings, all applied: tasks.md path, Opus eval 9 evidence, stale deltas, stale Phase 5 notes, PR body). Iter 4 (1 Copilot finding applied: followup_prompt period wording). Iter 5 (3 Copilot + 1 claude[bot] findings: benchmark.md nested backticks, benchmark.md eval 9 description, CLAUDE.md/copilot-instructions.md session-specific example, and a claude[bot] re-grade-rule catch that triggered a fresh Sonnet eval 9 re-run). Iter 6 (1 Copilot + 1 claude[bot] findings: Opus eval 9 evidence alignment, Opus 62%→38% reduction arithmetic). Iter 7 poll produced Copilot's explicit "reviewed 9 out of 9 changed files ... generated no new comments" review body — exit signal. Two unresolved threads remain (both declined mirror-rule design decisions from iter 2, by design).
- [x] **8.4** Run `/pr-human-guide` to annotate the PR for human reviewers. **Done** — appended a Review Guide to the PR body flagging 2 Novel Pattern items: (a) `skills/learn/SKILL.md` Step 4 (Preserve Cross-Config Sync Rules) — novel mirror-rule detection + reciprocation with deliberate user-choice-binds default, and (b) `evals/learn/evals.json` eval 9 `followup_prompt` field — first two-turn eval protocol in the suite. Other categories (Security / Config / New Deps / Data Model / Concurrency) produced no flagged items; data files and docs-only changes are excluded per `references/categories.md`.
- [ ] **8.5** Wait for human review. After human approval: squash-merge, delete branch, sync local main
