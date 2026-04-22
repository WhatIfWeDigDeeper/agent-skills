# learn Benchmark Results

**Models tested**: `claude-sonnet-4-6` (2026-03-14), `claude-opus-4-7` (2026-04-22)
**Evals**: 3 (1 run each per model per configuration — 12 runs total)

## Summary by model

### `claude-sonnet-4-6`

| Metric | with-skill | without-skill | Delta |
|--------|-----------|--------------|-------|
| Pass rate | **100.0%** ± 0.0% | 86.7% ± 23.1% | **+13%** |
| Time | 71.9s ± 10.8s | 46.1s ± 18.7s | +25.8s |
| Tokens | 16,008 ± 542 | 14,106 ± 3,512 | +1,902 |

The skill adds modest time and token overhead and improves correctness by +13 percentage points. The gap is concentrated in eval 2, where the skill correctly routes a multi-step workflow to a new skill file rather than appending it to config.

### `claude-opus-4-7`

| Metric | with-skill | without-skill | Delta |
|--------|-----------|--------------|-------|
| Pass rate | **100.0%** ± 0.0% | 100.0% ± 0.0% | **+0%** |
| Time | 83.5s ± 17.3s | 83.2s ± 38.2s | +0.2s |
| Tokens | 35,567 ± 862 | 28,032 ± 2,442 | +7,535 |

On Opus 4.7 the baseline reaches all 15 assertions on its own — including eval 2's multi-target routing and plan-before-apply, which were the skill's primary differentiator on Sonnet 4.6. Lift collapses to +0% on this model.

Summary-table Delta values are computed from unrounded means, so they may differ slightly from subtracting the displayed rounded means.

## Per-Eval Results

| # | Eval | Sonnet 4.6 with | Sonnet 4.6 without | Opus 4.7 with | Opus 4.7 without |
|---|------|-----------------|--------------------|---------------|------------------|
| 0 | CLAUDE.md update | 5/5 (100%) | 5/5 (100%) | 5/5 (100%) | 5/5 (100%) |
| 1 | New skill creation | 5/5 (100%) | 5/5 (100%) | 5/5 (100%) | 5/5 (100%) |
| 2 | Multi-target routing | 5/5 (100%) | **3/5 (60%)** | 5/5 (100%) | 5/5 (100%) |

**Only eval 2 on Sonnet 4.6 without-skill was discriminating** (bold above) — the baseline appended the 5-step workflow directly to both config files and skipped the pre-write plan step. That same eval is non-discriminating on Opus 4.7 because the Opus baseline now does both behaviors on its own.

## What Each Eval Tests

### Eval 0 — CLAUDE.md update
**Prompt**: Conversation where agent discovers `localhost` fails inside Docker containers; should save the `host.docker.internal` lesson to CLAUDE.md.

Tests the basic write path: learning is detected from the conversation, written to CLAUDE.md under a relevant section, and the agent summarizes what was added. All four runs succeeded — this is the simplest learning scenario (single target, clear fact).

### Eval 1 — New skill creation
**Prompt**: User describes a 4-step production deploy workflow (build, migrate, deploy, health check) with a 503 troubleshooting branch and asks to save it.

Tests the skill-creation route: the workflow is too procedural for a config file, so the agent should create a new `skills/deploy-prod/SKILL.md` with valid frontmatter and numbered steps. All four runs correctly chose to create a skill file rather than writing the full workflow to CLAUDE.md.

### Eval 2 — Multi-target routing
**Prompt**: Three learnings at once — a conftest.py discovery rule, a docker compose prerequisite, and a 5-step add-endpoint workflow — with both CLAUDE.md and `.github/copilot-instructions.md` present.

Tests multi-target detection and routing: factual rules go to both config files, the procedural workflow goes to a new skill, and a plan should be shown before writes. Only Sonnet 4.6 without-skill failed (3/5) — it appended the endpoint workflow directly to both config files and skipped the pre-write plan step. Opus 4.7 handles both correctly without the skill.

## Known Eval Limitations

- **Evals 0 and 1 are non-discriminating on both models.** They test the basic write path and skill-creation routing — both configurations succeed regardless of model.
- **Eval 2 only discriminates on Sonnet 4.6.** On Opus 4.7 the baseline already does multi-target routing and plan-before-apply on its own, so the skill adds no measurable lift under the current assertions.
- **Self-grading on Opus 4.7.** The Opus 4.7 runs were self-graded by the executor — no separate analyzer pass. Sonnet 4.6 runs used the original narrated/simulated grading methodology from the prior benchmark.
- **Next-step implication.** Producing a non-zero delta on Opus 4.7 would require new assertions targeting things baselines still miss — e.g. "one learning, one location" deduplication when content overlaps existing entries, disambiguation-prompt wording quality, or size-threshold-driven config-file splits.
