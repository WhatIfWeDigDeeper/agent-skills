# ship-it Benchmark Results

**Models tested**:
- `claude-sonnet-4-6` — 3 evals × 2 configurations on 2026-04-29 (spec 29). Analyzer: Sonnet 4.6.
- `claude-opus-4-7` — 3 evals × 2 configurations on 2026-04-29 (spec 29). Analyzer: **Sonnet 4.6** (analyzer-uniformity; Sonnet grades all 12 transcripts so per-model comparison is not confounded by analyzer-model differences).

**Evals**: 3 evals × 2 configurations × 2 models = **12 canonical runs**, all `run_number == 1`. Eval 3 (`branch-name-collision`) is excluded from this run set — its fixture requires a real git remote with `docs/update-readme` pre-existing, meaningfully more setup than the other three evals. See **Known Eval Limitations** below.

**Skill version**: v0.5. Both Sonnet and Opus were run under v0.5; the prior single-model benchmark predates this version's `metadata.skill_version` field, so all v0.x runs were retired and re-baselined at v0.5 for apples-to-apples comparison (see Known Eval Limitations).

## Summary

### `claude-sonnet-4-6`

| Metric | with-skill | without-skill | Delta |
|--------|-----------|---------------|-------|
| Pass rate | **100% ±0%** | 71% ±7% | **+29%** |
| Min / Max | 100% / 100% | 62% / 75% | |
| Time (s) | 51.2 ±4.7 | 35.5 ±9.8 | +15.8 |
| Tokens (input + output) | 2,364 ±172 | 1,506 ±191 | +859 |
| Cache tokens (creation + reads) | 583,183 ±88,814 | 228,081 ±59,358 | +355,102 |

Sonnet pass-rate delta is computed over 3 paired evals. Time, token, and cache-token statistics are computed from per-run subagent JSONL transcripts (`evals/scripts/extract_subagent_usage.py`); all 6 Sonnet runs have non-null measurements. Summary-table Delta values are computed from unrounded means, so they may differ slightly from subtracting the displayed rounded means.

### `claude-opus-4-7`

| Metric | with-skill | without-skill | Delta |
|--------|-----------|---------------|-------|
| Pass rate | **100% ±0%** | 62% ±12% | **+38%** |
| Min / Max | 100% / 100% | 50% / 75% | |
| Time (s) | 51.8 ±7.2 | 45.2 ±4.1 | +6.6 |
| Tokens (input + output) | 3,272 ±447 | 2,027 ±609 | +1,245 |
| Cache tokens (creation + reads) | 807,498 ±123,641 | 373,502 ±16,048 | +433,996 |

Opus pass-rate delta is computed over 3 paired evals. All 6 Opus runs have non-null measurements (extracted from subagent JSONL transcripts). Summary-table Delta values are computed from unrounded means, so they may differ slightly from subtracting the displayed rounded means.

The skill improves correctness on Sonnet 4.6 by **+29 percentage points** (71% → 100%) and on Opus 4.7 by **+38 percentage points** (62% → 100%). Opus's headline delta is *larger* than Sonnet's despite Opus being the stronger base model — Opus's baseline is paradoxically worse on this skill (62% vs Sonnet's 71%), driven by eval 1 (Opus 50% / Sonnet 75%) and eval 4 (Opus 62% / Sonnet 75%), where the Opus baseline made additional output-quality mistakes (skipping conventional-commit prefix on eval 1; producing a `## Summary` section without bullets — placing bullets under a separate `## Changes` heading — on eval 4) on top of the universally-failed process checks.

## Per-Eval Results

Each row shows passed/total per (model, configuration). Cells in **bold** are 100%; non-bold cells indicate the assertion set caught at least one failure.

| # | Eval | Sonnet 4.6 With | Sonnet 4.6 Without | Opus 4.7 With | Opus 4.7 Without |
|---|------|-----------------|--------------------|---------------|------------------|
| 1 | bug-fix-null-check | **8/8 (100%)** | 6/8 (75%) | **8/8 (100%)** | 4/8 (50%) |
| 2 | draft-pr-wip-feature | **8/8 (100%)** | 5/8 (62%) | **8/8 (100%)** | 6/8 (75%) |
| 4 | refactor-with-branch-name | **8/8 (100%)** | 6/8 (75%) | **8/8 (100%)** | 5/8 (62%) |

(Eval 3, `branch-name-collision`, is excluded from this run set — see Known Eval Limitations.)

## What Each Eval Tests

### Eval 1 — `bug-fix-null-check`
**Prompt**: `ship it`. User has uncommitted changes fixing null checks in a users API.

| Configuration | Sonnet 4.6 | Opus 4.7 |
|---------------|-----------|----------|
| with-skill    | **8/8 (100%)** | **8/8 (100%)** |
| without-skill | 6/8 (75%) | 4/8 (50%) |

**Discriminating** (Sonnet +0.25; Opus +0.50). Both `with_skill` configurations completed the full workflow including the divergence check, branch-collision check, and `--base` flag. The Sonnet `without_skill` agent skipped only the `git fetch` divergence check and the `git ls-remote` branch-collision check — it correctly produced a `fix/`-prefixed branch, a conventional commit, and a `## Summary` / `## Test Plan` PR body, AND it included `--base main` on `gh pr create` (an output-quality bullet that the prior single-model baseline reported as a discriminator — Sonnet now naturally produces it). The Opus `without_skill` agent failed those two process checks plus two output-quality assertions: it wrote a non-conventional commit message ("Add users API with null-safe getUser and updateUser" — no `fix:` prefix) and it omitted `--base` from `gh pr create`. The `--base` flag remains discriminating on Opus where it has flattened on Sonnet.

### Eval 2 — `draft-pr-wip-feature`
**Prompt**: `i'm done prototyping these onboarding changes — open a draft pr for me`.

| Configuration | Sonnet 4.6 | Opus 4.7 |
|---------------|-----------|----------|
| with-skill    | **8/8 (100%)** | **8/8 (100%)** |
| without-skill | 5/8 (62%) | 6/8 (75%) |

**Discriminating** (Sonnet +0.38; Opus +0.25). Draft-mode detection passes in both `without_skill` runs (the prompt's "draft pr" wording is unambiguous). The Sonnet baseline fails three assertions: `git fetch` divergence, `git ls-remote` branch check, and `## Test Plan` section (Sonnet's PR body had only a Summary section with no Test Plan). The Opus baseline fails only the two process checks — its PR body included an explicit `## Test Plan` section, surpassing Sonnet on that output-quality dimension.

### Eval 4 — `refactor-with-branch-name`
**Prompt**: `the auth refactor is done — ship it, call the branch refactor/auth-service`.

| Configuration | Sonnet 4.6 | Opus 4.7 |
|---------------|-----------|----------|
| with-skill    | **8/8 (100%)** | **8/8 (100%)** |
| without-skill | 6/8 (75%) | 5/8 (62%) |

**Discriminating** (Sonnet +0.25; Opus +0.38). Both baselines correctly preserved the user-specified branch name `refactor/auth-service` (assertion 1 passes) and produced a refactor-themed conventional commit and PR title (assertions 2 + 5 pass). The Sonnet baseline fails only the divergence and branch-collision checks. The Opus baseline fails those two plus assertion 3 (`## Summary` section with at least one bullet) — its PR body had a `## Summary` section but it contained only prose, not bullets; the bullets appeared under a separate `## Changes` heading. This is a structural miss against the assertion: the assertion requires bulleted content under `## Summary`, and Opus's baseline placed the bullets under the wrong heading. The miss is correctable by the skill (the `with_skill` Opus run produces bullets under `## Summary` directly), not a paraphrase artifact.

## Known Eval Limitations

### Discrimination structure

All 3 evals discriminate on both models — there are no zero-delta cells. The two universally-failing baseline assertions across all 6 `without_skill` runs are:

- `runs-divergence-check` — `git fetch` before push (every `without_skill` run on both models skipped this).
- `runs-ls-remote-branch-check` — branch-name collision check (every `without_skill` run on both models skipped this).

These two process checks are the structural discriminators of the ship-it skill. The third skill-defined process check, `gh-pr-create-uses-base-flag`, has flattened on Sonnet (it now passes in all 3 Sonnet `without_skill` runs) but remains discriminating on Opus (fails in eval 1 only). On Opus, additional output-quality variance also discriminates: eval 1 baseline misses `commit-is-conventional`, and eval 4 baseline misses `pr-body-has-summary`.

### Skill-version reset and prior eval_id correction

The pre-spec-29 benchmark recorded a `+38%` Sonnet delta with no `metadata.skill_version` field — its runs predated the skill's v0.5 release and several behavioral commits. All v-unspecified Sonnet runs were retired and re-baselined at v0.5 for apples-to-apples comparison with Opus 4.7. The new Sonnet headline at v0.5 is `+29%` (down from the prior `+38%`), reflecting both the v0.5 skill text and the Sonnet base model now naturally producing `--base` on `gh pr create`.

Pre-spec-29 `runs[]` also contained an `eval_id: 3` entry for the `refactor-with-branch-name` eval — a stale ID predating the addition of `branch-name-collision` (the actual id-3 eval) to `evals.json`. Spec 29 corrects this to `eval_id: 4` (matching `evals.json`); `metadata.evals_run` is now `[1, 2, 4]`.

### Eval 3 (`branch-name-collision`) gap

Eval 3's fixture requires a real git remote with the natural branch name (`docs/update-readme`) pre-existing, materially heavier setup than the other three evals (which need only a writable workspace and scripted `gh` interactions). Spec 29 deliberately leaves it un-run for the same reason prior benchmark passes did. Filling this gap is a candidate follow-up spec — both per-model `branch-name-collision` discrimination and the broader question of whether Opus 4.7 internalizes branch-name-suffixing behavior remain open.

### Per-model time/token measurements

All 12 runs have non-null `time_seconds`, `tokens`, and `cache_tokens` — they were extracted from subagent JSONL transcripts at `~/.claude/projects/.../subagents/agent-*.jsonl` via `evals/scripts/extract_subagent_usage.py`. No measurement gap on either model.

## Notes

### General (both models)

- **Eval 3 fixture cost**: see Known Eval Limitations above. The fixture cost gap also means `branch-name-suffixed` and `pr-created-on-suffixed-branch` assertions have no recorded data on either model.
- **`--base` flag flattened on Sonnet**: the prior single-model benchmark treated `gh-pr-create-uses-base-flag` as one of three universally-failing baseline assertions. At v0.5, Sonnet's baseline now produces `--base main` naturally in all 3 `without_skill` evals, leaving only two universally-failing checks (`git fetch` and `git ls-remote`). On Opus, `--base` still discriminates on eval 1.

### Sonnet 4.6

- **Headline shift from prior baseline**: the pre-spec-29 baseline reported `+38%` over a 6-run set with `branch-name-collision` mislabeled. The v0.5 baseline lands at `+29%` — the drop reflects both the natural improvement on `--base` and the fact that without-skill pass rates now vary across evals (62%/75%/75%) rather than being uniformly 62%.
- **Time/token measurements**: 6 of 6 runs have non-null measurements (extracted from subagent JSONL transcripts).

### Opus 4.7

- **Stronger headline delta despite weaker baseline**: Opus's `+38%` headline exceeds Sonnet's `+29%` despite Opus typically being the stronger base model. The driver is Opus's *worse* baseline on evals 1 and 4 — Opus skipped both process checks AND made an additional output-quality mistake on each of those evals (non-conventional commit on eval 1; `## Summary` section present but lacking bullets — bullets appeared under `## Changes` instead — on eval 4). The Opus `with_skill` runs still hit 100% across all 3 evals, so the skill closes a wider baseline gap.
- **Eval 2 baseline outperforms Sonnet's**: Opus's `without_skill` eval 2 scored 75% vs Sonnet's 62%. Opus's PR body included an explicit `## Test Plan` section that Sonnet's baseline omitted. Eval 2 is the only eval where Opus's baseline beats Sonnet's.
- **Time/token measurements**: 6 of 6 runs have non-null measurements.
