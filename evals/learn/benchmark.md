# learn Benchmark Results

**Models tested**: `claude-sonnet-4-6` (evals 0-2 dated 2026-03-14, eval 3 dated 2026-04-22), `claude-opus-4-7` (2026-04-22, evals 0-3)
**Evals**: 4 × 2 configurations × 2 models = 16 runs total, 1 run each.

## Summary by model

### `claude-sonnet-4-6`

| Metric | with-skill | without-skill | Delta |
|--------|-----------|--------------|-------|
| Pass rate | **100.0%** ± 0.0% | 90.0% ± 20.0% | **+10%** |
| Time | 67.8s ± 12.1s | 41.8s ± 17.6s | +26.0s |
| Tokens | 18,338 ± 4,681 | 15,080 ± 3,467 | +3,258 |

The skill's lift on Sonnet 4.6 is concentrated entirely in eval 2 (multi-target routing with plan-before-apply); evals 0, 1, and 3 all score 5/5 or 6/6 in both configurations. Adding the non-discriminating eval 3 diluted the prior 3-eval delta from +13% to +10% without changing what the skill actually fixes.

### `claude-opus-4-7`

| Metric | with-skill | without-skill | Delta |
|--------|-----------|--------------|-------|
| Pass rate | **100.0%** ± 0.0% | 100.0% ± 0.0% | **+0%** |
| Time | 74.1s ± 23.4s | 69.8s ± 41.2s | +4.3s |
| Tokens | 35,301 ± 882 | 27,239 ± 2,547 | +8,062 |

On Opus 4.7 the baseline reaches all 21 assertions per configuration on its own (5+5+5+6 across evals 0-3). Eval 2's multi-target routing and plan-before-apply — the sole Sonnet 4.6 differentiator — is handled by Opus without the skill. Eval 3's update-in-place behavior is also handled correctly. Lift is +0% across all four evals.

Summary-table Delta values are computed from unrounded means, so they may differ slightly from subtracting the displayed rounded means.

## Per-Eval Results

| # | Eval | Sonnet 4.6 with | Sonnet 4.6 without | Opus 4.7 with | Opus 4.7 without |
|---|------|-----------------|--------------------|---------------|------------------|
| 0 | CLAUDE.md update | 5/5 (100%) | 5/5 (100%) | 5/5 (100%) | 5/5 (100%) |
| 1 | New skill creation | 5/5 (100%) | 5/5 (100%) | 5/5 (100%) | 5/5 (100%) |
| 2 | Multi-target routing | 5/5 (100%) | **3/5 (60%)** | 5/5 (100%) | 5/5 (100%) |
| 3 | Update-in-place existing entry | 6/6 (100%) | 6/6 (100%) | 6/6 (100%) | 6/6 (100%) |

**Only eval 2 on Sonnet 4.6 without-skill is discriminating.** Evals 0, 1, and 3 are non-discriminating on both models. Eval 2 is non-discriminating on Opus 4.7.

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

### Eval 3 — Update-in-place existing entry
**Prompt**: User flags that an existing CLAUDE.md Commands bullet (`npm run build — build the app`) is misleading because it doesn't set `NODE_ENV=production` — the real production command is `npm run build:prod`.

Tests Route A's "search existing content before appending" rule: the correct behavior is to update the existing `npm run build` bullet in place (clarifying it's dev-only) and add a companion `build:prod` entry — not to append a new section while leaving the stale `build the app` description. All four runs (both configurations on both models) passed 6/6: every baseline updated in place, removed the stale "build the app" description, and explicitly described the update-in-place choice in its summary. The skill adds no measurable lift on this fixture.

## Known Eval Limitations

- **Evals 0, 1, and 3 are non-discriminating on both models.** They test the basic write path, skill-creation routing, and update-in-place behavior — all three are handled correctly by baselines at both tiers.
- **Eval 2 only discriminates on Sonnet 4.6.** On Opus 4.7 the baseline already does multi-target routing and plan-before-apply on its own, so the skill adds no measurable lift under the current assertions.
- **Self-grading.** All runs were self-graded by the executor — no separate analyzer pass. Sonnet 4.6 evals 0-2 used the original narrated/simulated grading methodology from the prior benchmark; eval 3 (Sonnet and Opus) used live-workspace self-grading. A separate grader pass would strengthen the null results, though the transcripts are unambiguous.
- **Next-step implication.** Update-in-place did not discriminate. Remaining candidates to pilot: timeless-rule stripping (user prompt includes session-specific details like "yesterday's PR #42"; skill should strip, baseline may preserve), and scope guard on multi-config broadcast (fixture with 3+ AI configs; skill should ask which to update, baseline may write to all without asking). If those also don't discriminate, the finding is that the current SKILL.md rules are largely internalized by Opus-tier baselines, and the skill's value on this model may be consistency across sessions rather than measurable single-shot lift.
