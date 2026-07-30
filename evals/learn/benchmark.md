# learn Benchmark Results

**Models tested**: `claude-sonnet-4-6` (evals 0-2 without_skill dated 2026-03-14, evals 3-4 without_skill dated 2026-04-22, all with_skill v1.0 and new evals 5/7/8 dated 2026-04-23), `claude-opus-4-7` (evals 0-4 without_skill dated 2026-04-22, all with_skill v1.0 and new evals 5/7/8 dated 2026-04-23), `claude-sonnet-5` and `claude-opus-5` (eval 9 only, both configurations, re-run at skill v1.3 on 2026-07-30).
**Evals**: 9 evals × 2 configurations × 2 models per eval = 36 runs total, 1 run each. Four new failure-mode evals (5 noise-rejection, 7 cross-assistant-sync, 8 silent-contradiction, 9 min-char-audit) were added at skill v1.0 alongside the original 0-4. Eval 6 (environment-scope-labeling) was drafted and dropped at the Phase 2 discrimination gate (both baselines scored 5/5 without_skill).

**Eval 9 was re-run at skill v1.3** on 2026-07-30 with a sixth assertion (`plan-shows-cut-in-audit`, 5 → 6). Its four rows **replaced** the v1.0 five-assertion entries rather than supplementing them, so the run total stays 36 and the eval count stays 9. `claude-sonnet-4-6` and `claude-opus-4-7` are no longer reachable from the runner (its model aliases now resolve to the Claude 5 family), so those rows executed on `claude-sonnet-5` / `claude-opus-5` and moved into their own model groups. **Evals 0-8 and eval 9 are therefore measured on different model generations.** Eval 9's with/without delta remains a valid paired comparison — both arms ran on the same model — but its absolute pass rates, character counts, timings, and token counts must not be compared against the v1.0 figures for evals 0-8. A same-model v1.2 control (below) exists specifically to break that confound.

## Summary by model

### `claude-sonnet-4-6` — evals 0-5, 7, 8 (v1.0)

| Metric | with-skill | without-skill | Delta |
|--------|-----------|--------------|-------|
| Pass rate | **100.0%** ± 0.0% | 80.0% ± 28.3% | **+20%** |
| Time | 59.4s ± 16.6s | 37.5s ± 18.7s | +21.8s |
| Tokens | 26,856 ± 1,216 | 16,696 ± 2,999 | +10,160 |

Across the 8 evals this group covers, the skill produces +20 pp pass-rate lift on Sonnet 4.6. Sonnet 4.6 eval 2 sentinel (multi-target routing + plan-before-apply) preserved: with-skill 5/5 vs without-skill 3/5 = +40 pp on that cell. Discriminating without_skill cells on Sonnet 4.6: eval 2 (3/5), eval 5 noise-rejection (1/5 — captured all 3 obvious items), eval 7 cross-assistant-sync (4/5 — missed reciprocal mirror-rule), eval 8 silent-contradiction (4/5 — transparent replace without conflict framing). Eval 9 is no longer in this group; it moved to `claude-sonnet-5` when it was re-run at v1.3, which is why this figure is +20 pp rather than the +22 pp published at v1.0.

### `claude-opus-4-7` — evals 0-5, 7, 8 (v1.0)

| Metric | with-skill | without-skill | Delta |
|--------|-----------|--------------|-------|
| Pass rate | **100.0%** ± 0.0% | 92.5% ± 10.4% | **+7%** |
| Time | 56.9s ± 14.2s | 51.7s ± 34.5s | +5.1s |
| Tokens | 36,764 ± 1,568 | 26,690 ± 1,862 | +10,074 |

Across the same 8 evals, the skill produces +7 pp lift on Opus 4.7. Baseline evals 0-4 still score 100% on Opus without-skill — the discrimination comes entirely from the failure-mode evals. Discriminating without_skill cells on Opus 4.7: eval 5 (4/5 — kept npm-install noise), eval 7 (4/5 — no reciprocal sync rule), eval 8 (4/5 — replaced without naming the conflict). Eval 9 moved to `claude-opus-5`, which is why this figure is +7 pp rather than the +11 pp published at v1.0.

### `claude-sonnet-5` — eval 9 only (v1.3, 1 run per configuration)

| Metric | with-skill | without-skill | Delta |
|--------|-----------|--------------|-------|
| Pass rate | **83.3%** | 33.3% | **+50%** |
| Time | 124.0s | 90.6s | +33.4s |
| Tokens | 6,622 | 5,640 | +982 |

### `claude-opus-5` — eval 9 only (v1.3, 1 run per configuration)

| Metric | with-skill | without-skill | Delta |
|--------|-----------|--------------|-------|
| Pass rate | **83.3%** | 50.0% | **+33%** |
| Time | 85.3s | 64.1s | +21.2s |
| Tokens | 6,568 | 4,389 | +2,179 |

Both Claude 5 groups hold a single run per configuration, so no standard deviation is defined (`stddev` is `null` in `benchmark.json` rather than `0`). Their deltas rest on one observation per cell.

Summary-table Delta values are computed from unrounded means, so they may differ slightly from subtracting the displayed rounded means.

**Token counts are not comparable across the model boundary.** The Claude 5 rows report 4,389–6,622 tokens against 11,968–39,013 for the v1.0 rows. That gap is a caching artifact, not a methodology change: per the repo convention `tokens` is `input_tokens + output_tokens` only, and near-total prompt caching pushes almost all input into cache reads instead — the four eval-9 runs recorded 561,012–1,098,032 cache tokens each (creation + reads, logged in their run `notes`) against headline `tokens` of 4,389–6,622. Never subtract a Claude 5 token figure from a 4.6/4.7 one.

**Note on `benchmark.json` metadata.** `metadata.executor_model` and `metadata.analyzer_model` are single-valued and cannot express four models. They name only the primary group — `claude-opus-4-7`, evals 0-8, dated 2026-04-23 — whose block the top-level `run_summary` mirrors per repo convention. `metadata.timestamp` (2026-07-30) and `metadata.skill_version` (1.3) instead describe the most recent runs in the file, eval 9's re-run on the Claude 5 models. **No run in this file was executed by `claude-opus-4-7` at v1.3.** Use each run's own `executor_model` field and `metadata.models_tested` for model attribution.

**Note on evidence paths.** The `evidence` strings in `benchmark.json` preserve each executor's actual path choice during its run and are not normalized across runs. Readers will see three path shapes referring to the same kind of artifact — a newly created skill file — depending on which directory the agent chose at write time: `skills/<name>/SKILL.md` (repo-canonical), `.claude/skills/<name>/SKILL.md` (Claude Code's symlink to `skills/`), and `outputs/skills/<name>/SKILL.md` (eval-workspace output). Divergence reflects real agent behavior across executors, not benchmark inconsistency.

## Per-Eval Results

| # | Eval | Sonnet with | Sonnet without | Opus with | Opus without |
|---|------|-------------|----------------|-----------|--------------|
| 0 | CLAUDE.md update | 5/5 (100%) | 5/5 (100%) | 5/5 (100%) | 5/5 (100%) |
| 1 | New skill creation | 5/5 (100%) | 5/5 (100%) | 5/5 (100%) | 5/5 (100%) |
| 2 | Multi-target routing | 5/5 (100%) | **3/5 (60%)** | 5/5 (100%) | 5/5 (100%) |
| 3 | Update-in-place existing entry | 6/6 (100%) | 6/6 (100%) | 6/6 (100%) | 6/6 (100%) |
| 4 | Scope-guard multi-config disambiguation | 6/6 (100%) | 6/6 (100%) | 6/6 (100%) | 6/6 (100%) |
| 5 | Noise rejection | 5/5 (100%) | **1/5 (20%)** | 5/5 (100%) | **4/5 (80%)** |
| 7 | Cross-assistant-sync | 5/5 (100%) | **4/5 (80%)** | 5/5 (100%) | **4/5 (80%)** |
| 8 | Silent contradiction | 5/5 (100%) | **4/5 (80%)** | 5/5 (100%) | **4/5 (80%)** |
| 9 | Min-char audit (two-turn) † | **5/6 (83%)** | **2/6 (33%)** | **5/6 (83%)** | **3/6 (50%)** |

Evals 0-8 ran on `claude-sonnet-4-6` / `claude-opus-4-7` at skill v1.0 with 5-6 assertions each. † Eval 9 ran on `claude-sonnet-5` / `claude-opus-5` at skill v1.3 with 6 assertions; its cells are not comparable to the rows above.

Eval 6 (environment-scope-labeling) was drafted and dropped at the Phase 2 gate — both baselines scored 5/5 without_skill because the prompt explicitly spelled out the local scope ("macOS keychain lost the secret key"), and baselines carried that scope forward into the rule text. It is not present in `evals.json` or `benchmark.json`.

## What Each Eval Tests

### Eval 0 — CLAUDE.md update
**Prompt**: Conversation where agent discovers `localhost` fails inside Docker containers; should save the `host.docker.internal` lesson to CLAUDE.md.

Tests the basic write path: learning is detected from the conversation, written to CLAUDE.md under a relevant section, and the agent summarizes what was added. Non-discriminating on both models at v1.0 (same as v0.9) — the simplest learning scenario has always been handled by both baselines.

### Eval 1 — New skill creation
**Prompt**: User describes a 4-step production deploy workflow (build, migrate, deploy, health check) with a 503 troubleshooting branch and asks to save it.

Tests the skill-creation route: the workflow is too procedural for a config file, so the agent should create a new `skills/<name>/SKILL.md` with valid frontmatter and numbered steps. Non-discriminating on both models — "3+ numbered steps" is a clear enough signal that baselines also create a skill.

### Eval 2 — Multi-target routing
**Prompt**: Three learnings at once — a conftest.py discovery rule, a docker compose prerequisite, and a 5-step add-endpoint workflow — with both CLAUDE.md and `.github/copilot-instructions.md` present.

Tests multi-target detection and routing: factual rules go to both config files, the procedural workflow goes to a new skill, and a plan should be shown before writes. The Sonnet 4.6 sentinel (with-skill 5/5 vs without-skill 3/5 = +40 pp) — Sonnet baseline appends the workflow directly to both configs and skips the plan step without the skill's explicit workflow. Opus 4.7 handles both branches without the skill.

### Eval 3 — Update-in-place existing entry
**Prompt**: User flags that an existing CLAUDE.md Commands bullet (`npm run build — build the app`) is misleading because it doesn't set `NODE_ENV=production` — the real production command is `npm run build:prod`.

Tests Route A's "search existing content before appending" rule and Principle 3 (one topic, one location). All four runs at v1.0 pass 6/6 — the update-in-place behavior is shared by both baselines and the skill on this fixture.

### Eval 4 — Scope-guard multi-config disambiguation
**Prompt**: Fixture with three AI configs (CLAUDE.md + `.github/copilot-instructions.md` + AGENTS.md); user shares a single git gotcha (`git reset --hard` + `git clean -fd`).

Tests Route A's multi-config disambiguation — detect all three, ask which to update, route to the chosen subset. All four runs at v1.0 pass 6/6. At v1.0 the skill also adds reciprocal mirror-rules to the three files via Step 4 when the user chooses "all"; that behavior is validated by eval 7, not by eval 4's assertion set.

### Eval 5 — Noise rejection
**Prompt**: Brain-dump with 4 learnings — 3 obvious ("npm install before npm start", "commit before switching branches", "read errors carefully") and 1 real (a staging deploy requires `--region us-west-2` to avoid the decommissioned default region/DB). Agent must save only the real one and explicitly name at least one rejected item.

Tests Principle 1 (reject noise). On Sonnet 4.6 without-skill the baseline captured all 3 obvious items and failed the reject assertions (1/5); on Opus 4.7 without-skill the baseline rejected 2 of 3 but kept the "npm install before npm start" bullet (4/5). With the skill, both models route all 3 obvious items to the rejection list and save only the staging-region rule (5/5 on both).

### Eval 7 — Cross-assistant-sync
**Prompt**: Fixture has both `CLAUDE.md` (containing a "keep `.github/copilot-instructions.md` in sync" mirror rule) and `.github/copilot-instructions.md` (no reciprocal rule). User shares a single backend test-command learning and asks to update all configs.

Tests the new Step 4 (Preserve Cross-Config Sync Rules). Both baselines without-skill preserved the existing sync rule in CLAUDE.md and applied the learning to both files — but neither added a reciprocal mirror-rule to copilot-instructions.md (4/5 on both models). With v1.0, Step 4 detects the missing reciprocal and adds it, and the summary names that Step 4 was applied (5/5 on both).

### Eval 8 — Silent contradiction
**Prompt**: CLAUDE.md already contains "After merging a PR, always `git pull` to sync local main". New learning: `git pull` leaves main divergent after a squash merge; use `git reset --hard origin/main` instead. User does not flag the existing rule.

Tests Principle 4 (surface contradictions explicitly). Both baselines without-skill replaced the rule in place and described the change transparently, but neither explicitly framed the replacement as a contradiction resolution (4/5 on both). With v1.0, the summary names the conflict ("supersedes the existing `git pull` rule because…") and identifies which version was kept and why (5/5 on both).

### Eval 9 — Min-char audit (two-turn)
**Prompt (turn 1)**: Verbose incident narrative (Thursday outage, 14hr impact) followed by a small concrete fix (a `test -w && touch && rm` write-probe + abort on failure). Turn 2: a pinned follow-up asking whether the rule is minimum-chars and either to affirm with `already minimal` (optional trailing period) or rewrite within 20%.

Tests whether the min-char audit fires on first pass. Primary signal: turn-1 rule body ≤ 200 chars. Corroboration: turn-2 is the pinned affirmation or a bounded rewrite that preserves both load-bearing clauses (the probe command and the abort behavior). Skill v1.3 added a sixth assertion, `plan-shows-cut-in-audit`: the turn-1 plan shown before any file write must carry a `Cut in audit:` line naming either the clauses removed or `none` with a per-clause defense.

**Observed at v1.3 (`claude-sonnet-5` / `claude-opus-5`, 2026-07-30):**

| Configuration | Model | Turn-1 rule chars | ≤ 200? | Turn 2 |
|---|---|---|---|---|
| with_skill | `claude-sonnet-5` | 243 | **no** | `already minimal`, nothing cut |
| with_skill | `claude-opus-5` | 270 | **no** | `already minimal`, nothing cut |
| without_skill | `claude-sonnet-5` | 384 | no | rewrite 384 → 245 (36.2% — outside the 20% bound) |
| without_skill | `claude-opus-5` | 378 | no | rewrite 378 → 305 (19.31% — inside the bound by 0.69 points) |

**`turn1-rule-under-200-chars` did not flip.** It fails with_skill on both models at v1.3. The 200-char threshold and the assertion wording were deliberately left unchanged rather than loosened to fit the result. The v1.0 with_skill runs measured 209 chars (`claude-sonnet-4-6`) and 308 chars (`claude-opus-4-7`), but those ran on a different model generation — **do not read 209 → 243 as a regression caused by v1.3.** The [v1.2 control](#v12-control-runs-same-model-ab) is the only same-model comparison in this file, and it shows the audit step did not shorten rules at all.

**What v1.3 does deliver is the plan trace.** `plan-shows-cut-in-audit` is fully discriminating: both with_skill runs emitted a well-formed `Cut in audit:` line in the turn-1 plan, and neither without_skill run showed a plan of any kind before writing (both opened by reporting the edit as already done). The artifact mechanism does what it was built to do — a skipped audit is now visible at plan time rather than inferable only from the rule's length. That is a real gain in transparency; it is not the gain the acceptance criterion measures.

**The audit is performed but does not bite.** The failure is not "the audit didn't fire" — it is visible and well-formed in both plans. The `claude-sonnet-5` run enumerated all four clauses, defended each in turn, and cut nothing. Running the audit does not by itself supply a forcing function that makes the agent actually cut.

Both with_skill runs land 5/6, failing only assertion 1. without_skill lands 2/6 on `claude-sonnet-5` (failing 1, 3, 5, 6) and 3/6 on `claude-opus-5` (failing 1, 5, 6). The lift therefore rests on narrative-stripping (assertion 5) and the new plan trace (assertion 6) on both models, plus the turn-2 bounded-rewrite limit (assertion 3) on Sonnet 5 only.

**Grading sensitivity on `without_skill` / `claude-opus-5`.** Two of that cell's six verdicts are close calls. Assertion 3 passed only because its 19.31% trim landed inside the 20% bound by 0.69 points — a near miss, not skill-driven restraint. Assertion 5 failed on the single literal token `silently` inside the rule body ("EFS throttling can silently flip a shard read-only"); a reviewer who read that as a mechanism clause rather than embedded incident narrative would grade the cell 4/6 instead of 3/6, which would move this group's pass-rate delta from **+0.33 to +0.17**. Both were graded strictly against the assertion text as written.

## v1.2 Control Runs (same-model A/B)

Eval 9's v1.3 rows changed skill version and model generation at the same time, so the v1.0 → v1.3 character counts cannot attribute anything to the audit step. To break that confound, eval 9 `with_skill` was run twice more on `claude-sonnet-5` and `claude-opus-5` against the pre-change skill — the whole `skills/learn/` directory extracted at commit `08bd629` (v1.2, including its `references/`) — with the same fixture, the same two-turn protocol, and the same character-counting method.

These two runs are **deliberately excluded from the `runs` array** in `benchmark.json`: they are neither `with_skill` at the current skill version nor `without_skill`, so including them would corrupt `run_summary`. They are recorded in the file's top-level `notes`.

### Result: the audit step did not shorten rules

| Model | v1.2 turn-1 | v1.3 turn-1 | Delta |
|---|---|---|---|
| `claude-sonnet-5` | 239 chars | 243 chars | **+4 (longer)** |
| `claude-opus-5` | 264 chars | 270 chars | **+6 (longer)** |

**This is a negative result for the change under test.** Formalizing the min-chars audit produced no reduction in turn-1 rule length on either model — marginally longer in both cases, and both still far above the 200-char target.

The reason is that **v1.2 already had a min-chars audit** (Step 5 plus Principle 5). The v1.2 `claude-opus-5` run narrated its cuts in prose ("Cut from the first draft during the minimum-viable-text audit: the 14-hour duration…") without any dedicated field. v1.3 therefore **formalized an existing behavior rather than introducing one**, which is why rule length did not move. What changed is that the cut list is now emitted as a machine-checkable field instead of optional prose — traceability, not compression.

### Directional turn-2 regression

At v1.2 both models found further cuts when challenged on minimality in turn 2; at v1.3 both answered `already minimal` and cut nothing.

| Model | v1.2 turn-1 → turn-2 | v1.3 turn-1 → turn-2 |
|---|---|---|
| `claude-sonnet-5` | 239 → 224 (6.3% trim) | 243 → 243 (`already minimal`) |
| `claude-opus-5` | 264 → **218** (17.4% trim) | 270 → 270 (`already minimal`) |

**The v1.2 `claude-opus-5` turn-2 rewrite at 218 chars is the closest any observed cell has come to the 200-char target — and it came from the version without the change.** The working hypothesis is that formalizing the audit raises the agent's confidence that its first draft is already minimal, suppressing the second-pass trim that was previously doing the useful work. This points the opposite way from the change's intent.

**Sample size: one run per cell.** This is directional, not conclusive, and it changes no recorded pass/fail — assertion 3 passes at both versions (v1.2's 6.3% and 17.4% trims are both inside the 20% bound; v1.3's affirmations match the pinned regex). It is worth a follow-up before the audit step is tuned further.

## Known Eval Limitations

- **Discrimination picture.** Across evals 0-8 at v1.0: on Sonnet 4.6 without-skill, 4 of 8 evals discriminate — 2 (60%), 5 (20%), 7 (80%), 8 (80%); on Opus 4.7 without-skill, 3 of 8 discriminate — 5 (80%), 7 (80%), 8 (80%). Eval 9 discriminates on both Claude 5 models at v1.3 (33% and 50% without-skill against 83% with). Baseline evals 0, 1, 3, 4 are non-discriminating on both v1.0 models — the behaviors they test (write path, skill-creation route, update-in-place, multi-config disambiguation) have all been internalized by modern baselines. They stay in the suite as regression sentinels, not as lift measurements.
- **Eval 9's ≤ 200-char assertion is a measured negative result at v1.3, not a false negative.** It fails with_skill on both models (243 chars on `claude-sonnet-5`, 270 on `claude-opus-5`) and the same-model v1.2 control shows why: the audit step did not shorten rules at all (239 → 243 and 264 → 270 — marginally *longer*). v1.2 already ran a min-chars audit; v1.3 formalized it as a `Cut in audit:` field rather than introducing it, so length did not move. Earlier revisions of this file described the failure as "the single known false-negative at v1.0", implying the assertion was mis-calibrated against behavior the skill was actually producing. The controlled comparison does not support that reading: the audit is performed and well-formed but does not bite, and the assertion is measuring that correctly. Holding the 200-char bar strict remains deliberate — loosening it would hide exactly this result. The eval still discriminates strongly (5/6 with-skill vs 2/6 and 3/6 without) on the strength of narrative-stripping, the turn-2 bound, and the new plan trace.
- **Directional evidence that v1.3 suppressed the turn-2 trim.** At v1.2 both models cut further when challenged on minimality (239 → 224, 264 → 218); at v1.3 both replied `already minimal` and cut nothing. The 218-char v1.2 cell is the closest any run has come to the target. One run per cell — directional, not conclusive. See [v1.2 Control Runs](#v12-control-runs-same-model-ab).
- **Grading provenance is mixed.** Evals 0-8 were self-graded by the executor with no separate analyzer pass, using live-workspace execution in isolated temp directories; evals 0-4 without-skill runs carry over from the v0.9 benchmark under the same methodology (Sonnet evals 0-2 have older narrated-grading artifacts preserved in `benchmark.json` notes). Eval 9's v1.3 rows were graded by four separate grader agents, one per run, each given the full assertion text and the executor transcript but never the skill. Two verdicts in the `without_skill` / `claude-opus-5` cell are close calls (see Eval 9 above).
- **The turn-2 affirmation assertion was tightened during PR review** from "first non-whitespace line matches" to "entire response matches". Runs affected were re-run rather than re-graded, per the evals/CLAUDE.md re-run-don't-re-grade rule; both v1.3 with_skill runs produced `already minimal` as the entire turn-2 response.
- **Interpretation.** Across evals 0-8 the skill produces +20 pp on Sonnet 4.6 and +7 pp on Opus 4.7, concentrated on judgment-call failure modes (noise rejection, cross-config mirror-rule reciprocation, explicit contradiction framing). Eval 9 adds +50 pp on Sonnet 5 and +33 pp on Opus 5 at v1.3, but on a single run per cell and against a baseline that shows no plan at all. **v1.3's contribution is transparency, not concision**: the `Cut in audit:` line makes a skipped audit visible at plan time, while the controlled comparison shows it produces no shorter rules and may suppress the second-pass trim. The skill may still provide value not captured here (consistency across sessions, cross-agent uniformity when multiple coding assistants collaborate on the same repo); that value is not visible in pass-rate deltas.
