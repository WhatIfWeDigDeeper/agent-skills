# learn Benchmark Results

**Model**: claude-sonnet-4-6
**Date**: 2026-03-14
**Evals**: 3 (1 run each, with-skill vs. without-skill)

## Summary

| Metric | with-skill | without-skill | Delta |
|--------|-----------|--------------|-------|
| Pass rate | **100.0%** ± 0.0% | 86.7% ± 23.1% | **+13%** |
| Time | 71.9s ± 10.8s | 46.1s ± 18.7s | +25.8s |
| Tokens | 16,008 ± 542 | 14,106 ± 3,512 | +1,902 |

The skill adds modest time and token overhead and improves correctness by +13 percentage points. The gap is concentrated in eval 2, where the skill correctly routes a multi-step workflow to a new skill file rather than appending it to config.

## Per-Eval Results

| # | Eval | with-skill | without-skill | Key differentiators |
|---|------|-----------|--------------|---------------------|
| 0 | CLAUDE.md update | **5/5 (100%)** | 5/5 (100%) | Tied — simple single-target write |
| 1 | New skill creation | **5/5 (100%)** | 5/5 (100%) | Tied — both created a valid SKILL.md |
| 2 | Multi-target routing | **5/5 (100%)** | 3/5 (60%) | Skill correctly routes workflow to new skill; baseline appended to config |

## What Each Eval Tests

### Eval 0 — CLAUDE.md update
**Prompt**: Conversation where agent discovers `localhost` fails inside Docker containers; should save the `host.docker.internal` lesson to CLAUDE.md.

Tests the basic write path: learning is detected from the conversation, written to CLAUDE.md under a relevant section, and the agent summarizes what was added. Both runs succeeded — this is the simplest learning scenario (single target, clear fact).

### Eval 1 — New skill creation
**Prompt**: User describes a 5-step production deploy workflow (build, migrate, deploy, health check, troubleshoot) and asks to save it.

Tests the skill-creation route: the workflow is too procedural for a config file, so the agent should create a new `skills/deploy/SKILL.md` with valid frontmatter and numbered steps. Both runs correctly chose to create a skill file rather than writing to CLAUDE.md.

### Eval 2 — Multi-target routing
**Prompt**: Three learnings at once — a conftest.py discovery rule, a docker compose prerequisite, and a 5-step add-endpoint workflow — with both CLAUDE.md and `.github/copilot-instructions.md` present.

Tests multi-target detection and routing: factual rules go to both config files, the procedural workflow goes to a new skill. The without-skill run failed by appending the endpoint workflow directly to both config files and skipping the pre-write plan step.

## Known Eval Limitations

- Evals are narrated/simulated — no live file system is modified during eval execution.
- Evals 0 and 1 are non-discriminating for the routing logic: both are single-learning scenarios that Claude handles well without skill guidance.
- The +13% delta understates skill value for complex multi-learning sessions; eval 2 is the most representative real-world case.
