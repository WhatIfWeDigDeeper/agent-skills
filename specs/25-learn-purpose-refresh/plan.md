# Spec 25: learn — purpose refresh for Opus-tier baselines

## Problem

The latest multi-model benchmark (committed on `evals/learn-opus-4-7-multi-model`, see `evals/learn/benchmark.json`) shows the skill has stopped discriminating on modern models:

| Metric | Sonnet 4.6 | Opus 4.7 |
|---|---|---|
| Pass-rate delta | **+8%** (was +13% with 3 evals; diluted by each non-discriminating addition) | **+0%** |
| Token overhead | +3,995 | +8,206 |
| Time overhead | +25.7s | +6.7s |

**19 of 20 eval cells are non-discriminating.** The sole discriminating cell is Sonnet 4.6 without-skill on eval 2 (multi-target routing). Both targeted discrimination attempts added in spec 24 and earlier passes — eval 3 (update-in-place) and eval 4 (scope-guard) — landed at 6/6 on every configuration. On Opus 4.7 eval 4 the baseline even produced a *more nuanced* scope-guard prompt than the skill: it reasoned that the Copilot file was style-scoped and recommended skipping it, rather than listing three configs as equal options.

The skill currently costs ~30% token overhead and measurable latency on Opus 4.7 with zero measured behavior change. The failure modes it was designed to prevent — forgetting multi-target routing, skipping plan-before-apply, appending duplicates, silently broadcasting to all configs — have been internalized by the base model.

## Design

### What the skill should target instead

Current evals all test the happy paths: a clear, well-formed learning arrives; the agent routes it correctly. Baselines pass these without instruction. The cases baselines are more likely to still fumble cluster around **judgment calls the skill's current NEVER list already names but no eval exercises**:

1. **Noise rejection** — session containing one real learning buried in 2–3 obvious facts ("npm install before running", "commit your work"). Baselines over-eagerly capture noise because each item individually looks like a learning. Correct behavior: save only the real one and state why the rest were rejected. The current skill has "NEVER extract basics" but no eval tests it.
2. **Environment-scope labeling** — a workaround scoped to a broken local setup (e.g., keyring unavailable forces `--no-gpg-sign`). Baselines globalize because the command-level fix reads universal. Correct behavior: annotate the scope condition so future sessions don't misapply it. The current skill has "NEVER treat one-off emergency fixes as universal rules" but no eval tests it.
3. **Cross-assistant config sync** — when both `CLAUDE.md` and `.github/copilot-instructions.md` are present and the user chooses to update both, the learning must land in both *and* both files' mirror-rules must reciprocate within the chosen subset. This repo's own `CLAUDE.md` encodes the rule ("keep `.github/copilot-instructions.md` in sync"), but the skill does not currently mention it. Eval 2 tests multi-target routing and plan-before-apply (detects multiple configs, asks which to update, routes workflow items to a skill vs. configs, shows the plan); eval 7 adds the mirror-rule preservation layer eval 2 does not cover — specifically, preserving the mirror-rule text during edits and adding the reciprocal rule to any chosen config that lacks it.
4. **Silent contradiction with existing content** — learning conflicts with a rule already in CLAUDE.md that the user hasn't flagged. Correct behavior: surface the conflict and propose replacement. Eval 3 tests update-in-place *when the user flags the stale entry*; this variant tests detection when the user doesn't.

### Skill rewrite direction

- **Trim the NEVER list.** Project CLAUDE.md explicitly flags heavy NEVERs as a yellow flag ("reframe and explain the reasoning"). Current skill has 7 NEVER items. Consolidate into five principles with explanations: *reject noise*, *annotate scope*, *one topic, one location*, *surface contradictions*, and the preserved spec-24 *minimum viable rule text* bullet. The NEVER framing should remain only where a hard rule is genuinely clearer than a principle.
- **Add a cross-assistant-sync step.** New Step (between current Step 3 Route and Step 4 Plan). **Scope: Markdown-based configs only** (`CLAUDE.md`, `GEMINI.md`, `AGENTS.md`, `.github/copilot-instructions.md`). Non-Markdown configs (`.cursor/rules/*.mdc`, `.continuerc.json`) are out of scope — mirror-rule detection and reciprocation in MDC/JSON is deferred to a follow-up spec. Within the Markdown scope: when multiple AI configs are present, check each for mirror-rule text referencing the others. When a learning is applied, operate only on the configs the user chose in the Step 1 disambiguation prompt — no fan-out. Within the chosen subset: preserve the mirror-rule text during edits, and add a reciprocal mirror-rule to any chosen config that lacks one.
- **Tighten Step 2's "ask yourself" block.** The three questions ("Would I forget this?", "Is this already covered?", "Is this universal or local?") are the skill's core judgment — they should be the first-class workflow, not a preamble. Move them ahead of the "scan for learnings" list so rejection is the default and inclusion is what earns an explanation.

### What stays

- Route A/B/C taxonomy works and matches how baselines already think. No change.
- Multi-config disambiguation prompt pattern — preserved. **User choice binds**: whichever configs the user picks are the only ones modified, even when mirror-rules in one config name another. The cross-sync step (new Step 4) operates only within the user's chosen subset. The prompt text may be augmented to surface detected mirror-rules as informational context, but the user's choice remains authoritative.
- Plan-before-apply step works on both models. No change.
- Size thresholds and refactoring reference. No change.

## New evals

Four new evals, each targeting one failure mode above. Goal: each has at least one assertion that fails without-skill on Opus 4.7.

### Eval 5 — noise rejection
**Prompt:** Session transcript containing 4 "learnings" — 3 obvious ("run `npm install` before `npm start`", "commit before pushing", "read errors carefully"), 1 real (project-specific flag). Correct behavior: save only the real one and state which were rejected and why.

**Discriminating assertion:** Final CLAUDE.md does not contain any of the 3 obvious items; summary explicitly names at least one rejected item.

### Eval 6 — environment-scope labeling
**Prompt:** User reports that `git commit` failed with GPG error until they added `--no-gpg-sign`, which fixed it. The scope is a broken local keyring, not a universal preference.

**Discriminating assertion:** The written rule labels the scope condition (e.g., "when GPG keyring is unavailable") rather than recommending `--no-gpg-sign` as default; no unconditional "always pass `--no-gpg-sign`" phrasing.

### Eval 7 — cross-assistant-sync rule
**Prompt:** Fixture has both `CLAUDE.md` and `.github/copilot-instructions.md`. CLAUDE.md contains a sync rule ("keep copilot-instructions.md in sync with changes here"). User shares a single learning (e.g., a test-runner flag) and responds `all` to the disambiguation prompt.

**Discriminating assertion:** Learning lands in both files; the sync rule in CLAUDE.md is preserved (not clobbered by a replace-section edit); copilot-instructions.md gains the reciprocal sync rule if it didn't have one. Summary mentions the sync was honored.

### Eval 8 — silent contradiction
**Prompt:** CLAUDE.md already contains a rule ("After merging a PR, always `git pull` to sync main"). User shares new learning: "just found out `git pull` can leave local main divergent after squash merge — need `git reset --hard origin/main` instead". User does not flag the existing rule.

**Discriminating assertion:** Agent detects the conflict and proposes updating the existing rule in place rather than appending a contradicting entry; summary explicitly names the contradiction and which version was kept.

## Skill changes

**File:** `skills/learn/SKILL.md`

### Changes summary

| Section | Change |
|---|---|
| `## Process` Step 2 | Promote "ask yourself" to lead the step; compress scan list |
| `## Process` — new step between current 3 and 4 | "Preserve Cross-Config Sync Rules" — detect mirror-rule text across configs and preserve/add it |
| `## NEVER` | Consolidate 7 bullets into five principles with reasoning |
| `## Guidelines` | Merge relevant NEVER items that became principles |
| `metadata.version` | Bump `"0.9"` → `"1.0"` (this is a significant workflow change, not patch) |

### What the new cross-sync step looks like (sketch)

```markdown
### 4. Preserve Cross-Config Sync Rules

When multiple configs are present, check each for text that references keeping
the others in sync (e.g., CLAUDE.md says "mirror changes to copilot-instructions.md").

**Interaction with the disambiguation prompt (Step 1):** the user's disambiguation
choice is authoritative. This step only operates on the configs the user chose to
update. Mirror-rules in an unchosen config do *not* cause fan-out to other configs.
When mirror-rules are detected, the disambiguation prompt may surface them
informationally so the user can make a deliberate choice, but the prompt does not
coerce the decision:

> Found multiple config files:
> 1. CLAUDE.md (142 lines) — contains mirror-rule referencing copilot-instructions.md
> 2. .github/copilot-instructions.md (38 lines)
>
> Which should I update? (enter number, or "all")

For each config the user chose to update:
- Apply each approved learning
- Do not clobber the mirror-rule text when editing the file; preserve it
- If the chosen config lacks a reciprocal mirror-rule naming the other chosen
  configs, add one

Configs the user did not choose are not modified.

**Why:** The mirror-rule is load-bearing — it is how future sessions know to sync.
Silently updating one config without the other, or deleting the mirror-rule during
a section rewrite, causes the configs to drift and the rule to die. User choice
still binds because the user may have legitimate reasons to scope a learning
narrowly (e.g., the Copilot file is style-scoped and the learning is not a style
rule).
```

### What the consolidated Guidelines/principles look like (sketch)

Replace the NEVER + Guidelines blocks with a single `## Principles` section:

1. **Reject noise; include only non-obvious lessons.** An agent that learns "npm install before npm start" trains itself to skim. If any developer already knows it, skip it. This explains why; the current NEVER rule just forbids it.
2. **Annotate scope; never globalize a one-off fix.** A workaround that worked today may harm tomorrow's session if the environment differs. Label the condition that triggered the fix so future agents can decide whether it applies.
3. **One topic, one location.** If a rule already exists anywhere in the config or a skill, update that entry. Two entries on the same topic create ambiguity — the agent follows whichever it reads first, which may be the weaker version.
4. **Surface contradictions; never silently duplicate.** If a learning conflicts with existing content, propose replacement with the conflict named. Silent contradictions cause inconsistent behavior depending on which rule the agent encounters first.
5. **Minimum viable rule text.** (Current spec-24 bullet — keep.)

## Files to Modify

| File | Change |
|---|---|
| `evals/learn/evals.json` | Add evals 5–8 with full assertion sets |
| `evals/learn/benchmark.json` | Append entries for each kept eval in 5–8 × 2 configs × 2 models (new `with_skill` runs from tasks 4.1/4.2; `without_skill` runs reused from Phase 2 tasks 2.1/2.3, not re-run in Phase 4); replace the v0.9 `with_skill` entries for evals 0–4 on both models at v1.0; update `evals_run`, `skill_version`, `run_summary`, `run_summary_by_model` |
| `evals/learn/benchmark.md` | Update `**Models tested**` header line (v1.0 re-run dates), update `**Evals**` total-count line, update `## Per-Eval Results` table (new rows for kept evals, updated rows for 0–4 at v1.0), add per-eval sections for each kept eval in 5–8, update Summary tables, reconcile the token-denominator note (M = 5 → 5 + K, combined = 10 → 10 + 2K — add only if the final run set is partially populated), update `## Known Eval Limitations` section (replace the 19-of-20 framing with the new discrimination picture) |
| `skills/learn/SKILL.md` | Rewrite Step 2; add cross-sync step; consolidate NEVER/Guidelines into Principles; bump version |
| `README.md` | Update Eval Δ column and learn Skill Notes `Eval cost` bullet |
| `cspell.config.yaml` | Add any new unknown words |

## Branch

`evals/learn-purpose-refresh`

## Verification

1. Every kept new eval discriminates on Opus 4.7: at least one assertion fails without-skill on Opus 4.7. Non-discriminating evals were dropped in Phase 2 per the gate, not carried forward.
2. `metadata.skill_version` in `benchmark.json` matches `metadata.version` in `SKILL.md` ("1.0").
3. All v0.9 `with_skill` run entries for evals 0–4 were replaced per task 4.3; `metadata.skill_version` is `"1.0"`. (Per-run `skill_version` is not recorded in the current schema, so this is a process check plus the count-based verification in 6.14.)
4. `evals_run` lists the final post-gate eval ID set (baseline 0–4 plus the kept subset of 5–8).
5. `uv run --with pytest pytest tests/` — no regressions.
6. `npx cspell README.md skills/learn/SKILL.md evals/learn/benchmark.md specs/25-learn-purpose-refresh/*.md` — clean.
7. README.md `Eval Δ` for learn matches per-model deltas from `run_summary_by_model[<model>].delta.pass_rate` (rounded) — the README shows per-model values, not the top-level `run_summary.delta.pass_rate` (which mirrors only the latest model).
8. `benchmark.md` Summary-table `±` values mirror `run_summary` / `run_summary_by_model` exactly.
9. `benchmark.md` `**Models tested**` header includes v1.0 re-run dates for both models.
10. `benchmark.md` `**Evals**` total-count line reflects 5 + K evals and 4·(5+K) runs total.
11. `benchmark.md` `## Per-Eval Results` table has a row for every kept eval in 5–8 and updated v1.0 rows for evals 0–4.
12. `benchmark.md` `## Known Eval Limitations` no longer uses the 19-of-20 non-discriminating framing.

## Shipping

1. Work on branch `evals/learn-purpose-refresh` (branch off current `evals/learn-opus-4-7-multi-model` only if unmerged; otherwise off main after that ships).
2. Open PR; run `/pr-comments` after creation.
3. Squash-merge, delete branch, sync local main.

## Risks

- **New evals may not discriminate as expected.** Opus 4.7 baseline is strong; it may handle noise rejection, scope labeling, and contradiction detection on its own. Phase 2 of the task list is a validation gate — if a new eval doesn't discriminate, either strengthen the prompt (bury the real signal deeper; make the contradiction subtler) or drop the eval rather than carry a non-discriminating test.
- **Cross-sync behavior is meta.** The skill is being asked to honor a rule *written in the config it is editing*. If the rule text varies across projects, the detection may miss. Keep the check tolerant: look for the word pairs `keep ... in sync` or `mirror ... to` near another config's filename.
- **Principle rewrite may lose enforcement strength.** Consolidating NEVERs into principles is the riskiest change. Mitigation: keep the current Sonnet 4.6 eval 2 lift (+40 pp on that cell) after the rewrite — it's our sentinel for "did the skill still teach the thing."
- **Scope creep.** This spec touches evals, the skill, and README/benchmark.md. Hold the line at the four failure modes above; do not also rewrite the reference files (`assistant-configs.md`, `refactoring.md`) in the same PR.
