# learn Benchmark Results

**Models tested**: `claude-sonnet-4-6` (evals 0-2 without_skill dated 2026-03-14, evals 3-4 without_skill dated 2026-04-22, all with_skill v1.0 and new evals 5/7/8/9 dated 2026-04-23), `claude-opus-4-7` (evals 0-4 without_skill dated 2026-04-22, all with_skill v1.0 and new evals 5/7/8/9 dated 2026-04-23)
**Evals**: 9 × 2 configurations × 2 models = 36 runs total, 1 run each. Four new failure-mode evals (5 noise-rejection, 7 cross-assistant-sync, 8 silent-contradiction, 9 min-char-audit) were added at skill v1.0 alongside the original 0-4. Eval 6 (environment-scope-labeling) was drafted and dropped at the Phase 2 discrimination gate (both baselines scored 5/5 without_skill).

## Summary by model

### `claude-sonnet-4-6`

| Metric | with-skill | without-skill | Delta |
|--------|-----------|--------------|-------|
| Pass rate | **95.6%** ± 13.3% | 75.6% ± 29.6% | **+20%** |
| Time | 59.6s ± 15.6s | 37.6s ± 17.5s | +22.0s |
| Tokens | 26,825 ± 1,141 | 16,979 ± 2,931 | +9,846 |

At v1.0 the skill produces +20 pp pass-rate lift across 9 evals on Sonnet 4.6 (was +8 pp at v0.9 across 5 evals). Sonnet 4.6 eval 2 sentinel (multi-target routing + plan-before-apply) preserved: with-skill 5/5 vs without-skill 3/5 = +40 pp on that cell. Discriminating without_skill cells on Sonnet: eval 2 (3/5), eval 5 noise-rejection (1/5 — captured all 3 obvious items), eval 7 cross-assistant-sync (4/5 — missed reciprocal mirror-rule), eval 8 silent-contradiction (4/5 — transparent replace without conflict framing), eval 9 min-char-audit (2/5 — 370-char rule + 38% trim + embedded incident narrative).

### `claude-opus-4-7`

| Metric | with-skill | without-skill | Delta |
|--------|-----------|--------------|-------|
| Pass rate | **97.8%** ± 6.7% | 86.7% ± 20.0% | **+11%** |
| Time | 58.0s ± 13.7s | 50.5s ± 32.5s | +7.5s |
| Tokens | 36,823 ± 1,478 | 26,739 ± 1,748 | +10,083 |

At v1.0 the skill produces +11 pp pass-rate lift on Opus 4.7 (was +0 pp at v0.9). Baseline evals 0-4 still score 100% on Opus without-skill — the discrimination now comes entirely from the four new failure-mode evals. Discriminating without_skill cells on Opus: eval 5 (4/5 — kept npm-install noise), eval 7 (4/5 — no reciprocal sync rule), eval 8 (4/5 — replaced without naming the conflict), eval 9 (2/5 — 494-char rule body, 45% over-trim in turn-2, embedded incident narrative).

Summary-table Delta values are computed from unrounded means, so they may differ slightly from subtracting the displayed rounded means.

**Note on evidence paths.** The `evidence` strings in `benchmark.json` preserve each executor's actual path choice during its run and are not normalized across runs. Readers will see three path shapes referring to the same kind of artifact — a newly created skill file — depending on which directory the agent chose at write time: `skills/<name>/SKILL.md` (repo-canonical), `.claude/skills/<name>/SKILL.md` (Claude Code's symlink to `skills/`), and `outputs/skills/<name>/SKILL.md` (eval-workspace output). Divergence reflects real agent behavior across executors, not benchmark inconsistency.

## Per-Eval Results

| # | Eval | Sonnet 4.6 with | Sonnet 4.6 without | Opus 4.7 with | Opus 4.7 without |
|---|------|-----------------|--------------------|---------------|------------------|
| 0 | CLAUDE.md update | 5/5 (100%) | 5/5 (100%) | 5/5 (100%) | 5/5 (100%) |
| 1 | New skill creation | 5/5 (100%) | 5/5 (100%) | 5/5 (100%) | 5/5 (100%) |
| 2 | Multi-target routing | 5/5 (100%) | **3/5 (60%)** | 5/5 (100%) | 5/5 (100%) |
| 3 | Update-in-place existing entry | 6/6 (100%) | 6/6 (100%) | 6/6 (100%) | 6/6 (100%) |
| 4 | Scope-guard multi-config disambiguation | 6/6 (100%) | 6/6 (100%) | 6/6 (100%) | 6/6 (100%) |
| 5 | Noise rejection | 5/5 (100%) | **1/5 (20%)** | 5/5 (100%) | **4/5 (80%)** |
| 7 | Cross-assistant-sync | 5/5 (100%) | **4/5 (80%)** | 5/5 (100%) | **4/5 (80%)** |
| 8 | Silent contradiction | 5/5 (100%) | **4/5 (80%)** | 5/5 (100%) | **4/5 (80%)** |
| 9 | Min-char audit (two-turn) | **3/5 (60%)** | **2/5 (40%)** | **4/5 (80%)** | **2/5 (40%)** |

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
**Prompt**: CLAUDE.md already contains `After merging a PR, always `git pull` to sync local main`. New learning: `git pull` leaves main divergent after a squash merge; use `git reset --hard origin/main` instead. User does not flag the existing rule.

Tests Principle 4 (surface contradictions explicitly). Both baselines without-skill replaced the rule in place and described the change transparently, but neither explicitly framed the replacement as a contradiction resolution (4/5 on both). With v1.0, the summary names the conflict ("supersedes the existing `git pull` rule because…") and identifies which version was kept and why (5/5 on both).

### Eval 9 — Min-char audit (two-turn)
**Prompt (turn 1)**: Verbose incident narrative (Thursday outage, 14hr impact) followed by a small concrete fix (a `test -w && touch && rm` write-probe + abort on failure). Turn 2: a pinned follow-up asking whether the rule is minimum-chars and either to affirm with the exact string `already minimal.` or rewrite within 20%.

Tests whether the Plan-step min-char audit (task 3.3) fires on first pass. Primary signal: turn-1 rule body ≤ 200 chars. Corroboration: turn-2 is the pinned affirmation or a bounded rewrite that preserves both load-bearing clauses (the probe command and the abort behavior).

Both baselines without-skill fail on 3 of 5 assertions (2/5): turn-1 rule bodies were 494 chars (Opus) and 370 chars (Sonnet), both embedded incident narrative ("14hr outage", "incident: 14h search relevance degradation"), and both turn-2 rewrites trimmed 38-45% — well outside the 20% bound. With v1.0 the audit fires and strips the narrative (Opus turn-1 308 chars; Sonnet turn-1 253 chars; both preserve the probe + abort). Opus with-skill turn-2 rewrites within the 20% bound (308 → 276 chars, 10.4% trim) and lands 4/5. Sonnet with-skill turn-2 produced a multi-paragraph clause-by-clause analysis ending in `**already minimal.**` — which satisfies the original loose assertion (first-line match) but not the tightened assertion applied during PR review (entire response must be the pinned affirmation). Sonnet with-skill therefore lands 3/5: the affirmation branch fails on the extra prose and the bounded-rewrite branch doesn't apply because no rewrite was produced. **The turn-1 ≤ 200-char assertion still fails at v1.0 on both models** — the audit fires but doesn't get below 200 on first pass. That is one of two known false-negatives for this eval (the second is the Sonnet multi-paragraph affirmation pattern). The primary-signal strictness is intentional (see plan.md Eval 9 spec); the audit's measurable effect is visible in the 62% (Opus) / 46% (Sonnet) turn-1 length reduction versus the baseline, and the rewrite/narrative-stripping clauses still flip to pass on both models.

## Known Eval Limitations

- **Discrimination picture at v1.0 (9 evals × 2 models = 18 cells per configuration).** On Sonnet 4.6 without-skill, 5 of 9 evals discriminate: 2 (60%), 5 (20%), 7 (80%), 8 (80%), 9 (40%). On Opus 4.7 without-skill, 4 of 9 evals discriminate: 5 (80%), 7 (80%), 8 (80%), 9 (40%). Baseline evals 0, 1, 3, 4 are non-discriminating on both models — the behaviors they test (write path, skill-creation route, update-in-place, multi-config disambiguation) have all been internalized by modern baselines. They stay in the suite as regression sentinels, not as lift measurements.
- **Eval 9 has two known false-negatives at v1.0.** (1) The turn-1 ≤ 200-char assertion fails on both models — the Plan-step audit fires and cuts the incident narrative, but the resulting rule body (308 chars Opus, 253 chars Sonnet) still exceeds the 200-char primary-signal threshold. (2) The Sonnet with_skill turn-2 affirmation produces multi-paragraph prose ending in `**already minimal.**` — under the tightened assertion (entire response must be the pinned affirmation; applied during PR review), this fails the affirmation branch and, because no rewrite was produced, the bounded-rewrite branch doesn't apply either. The eval still discriminates strongly on both models (Opus 4/5 with-skill vs 2/5 without = +40 pp; Sonnet 3/5 with-skill vs 2/5 without = +20 pp) because the probe-clause preservation, narrative-stripping, and (on Opus) bounded-rewrite clauses all shift from fail to pass. Holding the primary-signal and affirmation bars strict is a deliberate choice (plan.md Eval 9): loosening either would weaken the signal that the audit ran unprompted.
- **Self-grading.** All runs were self-graded by the executor — no separate analyzer pass. With-skill runs and Phase 2 without-skill runs for new evals used live-workspace self-grading in isolated temp directories. Evals 0-4 without-skill runs carry over from the v0.9 benchmark and used the same methodology (live-workspace; Sonnet evals 0-2 have older narrated-grading artifacts preserved in `benchmark.json` notes).
- **Interpretation.** At v1.0 the skill moves from "no measurable lift on modern baselines" to a meaningful +20 pp on Sonnet 4.6 and +11 pp on Opus 4.7 — concentrated entirely on judgment-call failure modes (noise rejection, cross-config mirror-rule reciprocation, explicit contradiction framing, unprompted min-char audit). The skill may still provide value not captured here (consistency across sessions, cross-agent uniformity when multiple coding assistants collaborate on the same repo); that value is not visible in pass-rate deltas.
