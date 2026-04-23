# learn Benchmark Results

**Models tested**: `claude-sonnet-4-6` (evals 0-2 dated 2026-03-14, evals 3-4 dated 2026-04-22), `claude-opus-4-7` (2026-04-22, evals 0-4)
**Evals**: 5 × 2 configurations × 2 models = 20 runs total, 1 run each.

## Summary by model

### `claude-sonnet-4-6`

| Metric | with-skill | without-skill | Delta |
|--------|-----------|--------------|-------|
| Pass rate | **100.0%** ± 0.0% | 92.0% ± 17.9% | **+8%** |
| Time | 72.1s ± 14.3s | 46.4s ± 18.4s | +25.7s |
| Tokens | 20,143 ± 5,720 | 16,148 ± 3,835 | +3,995 |

The skill's lift on Sonnet 4.6 is concentrated entirely in eval 2 (multi-target routing with plan-before-apply); evals 0, 1, 3, and 4 all score 5/5 or 6/6 in both configurations. Adding non-discriminating evals 3 and 4 diluted the headline delta from +13% (3 evals) to +10% (4 evals) to +8% (5 evals) without changing what the skill actually fixes.

### `claude-opus-4-7`

| Metric | with-skill | without-skill | Delta |
|--------|-----------|--------------|-------|
| Pass rate | **100.0%** ± 0.0% | 100.0% ± 0.0% | **+0%** |
| Time | 73.2s ± 20.4s | 66.5s ± 36.4s | +6.7s |
| Tokens | 35,409 ± 802 | 27,204 ± 2,208 | +8,206 |

On Opus 4.7 the baseline reaches all 27 assertions per configuration (5+5+5+6+6 across evals 0-4) on its own. Every behavior the skill is designed to enforce — multi-target routing, plan-before-apply, update-in-place, scope-guard disambiguation on multi-config fixtures — is handled by the Opus baseline without the skill. On eval 4 the baseline prompt was even more nuanced than the skill's, noting that one of the three configs was style-scoped and recommending it be skipped. Lift is +0% across all five evals.

Summary-table Delta values are computed from unrounded means, so they may differ slightly from subtracting the displayed rounded means.

**Note on evidence paths.** The `evidence` strings in `benchmark.json` preserve each baseline's actual path choice during its run and are not normalized across runs. Readers will see three path shapes referring to the same kind of artifact — a newly created skill file — depending on which directory the agent chose at write time: `skills/<name>/SKILL.md` (repo-canonical), `.claude/skills/<name>/SKILL.md` (Claude Code's symlink to `skills/`), and `outputs/skills/<name>/SKILL.md` (eval-workspace output). Divergence reflects real agent behavior across executors, not benchmark inconsistency.

## Per-Eval Results

| # | Eval | Sonnet 4.6 with | Sonnet 4.6 without | Opus 4.7 with | Opus 4.7 without |
|---|------|-----------------|--------------------|---------------|------------------|
| 0 | CLAUDE.md update | 5/5 (100%) | 5/5 (100%) | 5/5 (100%) | 5/5 (100%) |
| 1 | New skill creation | 5/5 (100%) | 5/5 (100%) | 5/5 (100%) | 5/5 (100%) |
| 2 | Multi-target routing | 5/5 (100%) | **3/5 (60%)** | 5/5 (100%) | 5/5 (100%) |
| 3 | Update-in-place existing entry | 6/6 (100%) | 6/6 (100%) | 6/6 (100%) | 6/6 (100%) |
| 4 | Scope-guard multi-config disambiguation | 6/6 (100%) | 6/6 (100%) | 6/6 (100%) | 6/6 (100%) |

**Only eval 2 on Sonnet 4.6 without-skill is discriminating.** The other 19 cells all pass 100%.

## What Each Eval Tests

### Eval 0 — CLAUDE.md update
**Prompt**: Conversation where agent discovers `localhost` fails inside Docker containers; should save the `host.docker.internal` lesson to CLAUDE.md.

Tests the basic write path: learning is detected from the conversation, written to CLAUDE.md under a relevant section, and the agent summarizes what was added. All four runs succeeded — this is the simplest learning scenario (single target, clear fact).

### Eval 1 — New skill creation
**Prompt**: User describes a 4-step production deploy workflow (build, migrate, deploy, health check) with a 503 troubleshooting branch and asks to save it.

Tests the skill-creation route: the workflow is too procedural for a config file, so the agent should create a new `skills/<name>/SKILL.md` with valid frontmatter and numbered steps. Observed names across runs vary (`deploy`, `deploy-prod`); the assertion requires a new skill file, not a specific name. All four runs correctly chose to create a skill file rather than writing the full workflow to CLAUDE.md.

### Eval 2 — Multi-target routing
**Prompt**: Three learnings at once — a conftest.py discovery rule, a docker compose prerequisite, and a 5-step add-endpoint workflow — with both CLAUDE.md and `.github/copilot-instructions.md` present.

Tests multi-target detection and routing: factual rules go to both config files, the procedural workflow goes to a new skill, and a plan should be shown before writes. Only Sonnet 4.6 without-skill failed (3/5) — it appended the endpoint workflow directly to both config files and skipped the pre-write plan step. Opus 4.7 handles both correctly without the skill.

### Eval 3 — Update-in-place existing entry
**Prompt**: User flags that an existing CLAUDE.md Commands bullet (`npm run build — build the app`) is misleading because it doesn't set `NODE_ENV=production` — the real production command is `npm run build:prod`.

Tests Route A's "search existing content before appending" rule: the correct behavior is to update the existing `npm run build` bullet in place (clarifying it's dev-only) and add a companion `build:prod` entry — not to append a new section while leaving the stale `build the app` description. All four runs (both configurations on both models) passed 6/6: every baseline updated in place, removed the stale "build the app" description, and explicitly described the update-in-place choice in its summary. The skill adds no measurable lift on this fixture.

### Eval 4 — Scope-guard multi-config disambiguation
**Prompt**: Fixture with three AI configs (CLAUDE.md + `.github/copilot-instructions.md` + AGENTS.md); user shares a single git gotcha (`git reset --hard` + `git clean -fd`).

Tests Route A's scope-guard behavior on multi-config fixtures: the skill's expected behavior is to detect all three configs, explicitly ask the user which to update, and only then write. All four runs (both configurations on both models) passed 6/6: every baseline detected all three configs, emitted a numbered-choice disambiguation prompt before writing, and wrote to the chosen subset. Notably, the Opus 4.7 baseline prompt was more nuanced than the skill's — it reasoned that the Copilot file was style-scoped and recommended skipping it, rather than just listing all three as equal options. The skill adds no measurable lift on this fixture.

## Known Eval Limitations

- **19 of 20 cells are non-discriminating.** Evals 0, 1, 3, and 4 are non-discriminating on both models. Eval 2 is non-discriminating on Opus 4.7. Only Sonnet 4.6 without-skill on eval 2 produces a fail verdict (3/5) — that single cell drives the entire measured lift.
- **Discrimination attempts for Opus 4.7 failed.** Evals 3 (update-in-place) and 4 (scope-guard) were designed as targeted discrimination tests for Opus-tier baselines and did not discriminate. Both Sonnet and Opus baselines already internalize Route A's "search before appending" and "ask which configs" rules — they do the right thing without the skill's explicit instruction.
- **Self-grading.** All runs were self-graded by the executor — no separate analyzer pass. Sonnet 4.6 evals 0-2 used the original narrated/simulated grading methodology from the prior benchmark; evals 3-4 used live-workspace self-grading. A separate grader pass would strengthen the null results, though the transcripts are unambiguous.
- **Interpretation.** Opus-tier baselines now handle everything the skill is currently designed to enforce. The skill's measurable single-shot value on this model is effectively zero under the current assertion set. The skill may still provide value not captured here (consistency across sessions with different prompts; cross-agent uniformity when multiple coding assistants collaborate on the same repo; latency of reference-file reads preventing certain failure modes the evals don't simulate) — but that value is not visible in pass-rate deltas.
