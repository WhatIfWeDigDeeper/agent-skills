# pr-human-guide Benchmark Results

**Models tested**:
- `claude-sonnet-4-6` — full 8-eval suite × 2 configurations on 2026-04-28 (spec 28). Analyzer: **Sonnet 4.6**.
- `claude-opus-4-7` — full 8-eval suite × 2 configurations on 2026-04-28 (spec 28). Analyzer: **Sonnet 4.6** (chosen up front for analyzer-uniformity, following the spec 27 precedent).
- `claude-opus-4-8` — partial set: 6 evals (9–14) × 2 configurations on Opus 4.8 (evals 9–12 on 2026-06-28, spec 48; evals 13–14 on 2026-07-04, spec 50). Analyzer: **Opus 4.8** (graded inline by the controller). Evals 9–12 cover the two impact-risk Novel Patterns signals (sweeping cross-cutting refactor, high-fanout core helper edit), a negative rename guardrail, and the Selectivity Threshold; evals 13–14 cover the refined operative-skill-source exemption (a positive trust-boundary case in a `skills/**/references/*.md` file, and a negative pure-wording case). See the v0.13 and v0.14 subsections under Known Eval Limitations.
- `claude-opus-5` — partial set: 3 evals (15–17) × 2 configurations (eval 15 on 2026-08-15, spec 56; evals 16–17 on 2026-08-16, spec 57). Analyzer: **Opus 5** (eval 15 graded inline by the controller; evals 16–17 by dedicated grader subagents). Eval 15 covers checked-state preservation across a re-run: one item whose anchored content is unchanged must stay ticked, one whose content was rewritten must reset. Evals 16–17 cover Documentation Drift, one per branch: a rename that leaves an untouched `README.md` stale, and the same rename with the doc updated in the same diff. See the v0.16 and v0.17 subsections under Known Eval Limitations.

**Evals**: 8 evals × 2 configurations × 2 models = **32 canonical runs** (the full-suite headline), plus **12 partial-set runs** (evals 9–14 × 2 configurations on Opus 4.8, specs 48+50) and **6 partial-set runs** (evals 15–17 × 2 configurations on Opus 5, specs 56+57) = 50 runs total, all `run_number == 1`.

**Skill version**: full-suite rows under v0.7; the spec-48 partial set (evals 9–12) under v0.13; the spec-50 additions (evals 13–14) under v0.14; the spec-56 addition (eval 15) under v0.16; the spec-57 additions (evals 16–17) under v0.17. The previous Sonnet runs at v0.1 (16 entries) were removed in spec 28 Phase 1 so both full-suite models share an apples-to-apples skill version; git history retains the prior shape. `benchmark.json` `metadata.skill_version` is `"0.17"` as of spec 57 — the earlier `"0.7"` pin (rationalized as "the version of the recorded full-suite runs") is drift from the written rule in `evals/CLAUDE.md`, which requires advancing it whenever runs are added. Each partial set remains version-noted here and in its own subsection, which is where per-set versions are authoritative.

## Summary

### `claude-sonnet-4-6`

| Metric | with-skill | without-skill | Delta |
|--------|------------|---------------|-------|
| Pass rate | **100%** ±0% | 69% ±24% | **+31%** |
| Min / Max | 100% / 100% | 33% / 100% | |
| Time (s) | 60.9 ±7.9 | 43.5 ±12.5 | +17.4 |
| Tokens (input + output) | 3,147 ±765 | 2,311 ±967 | +835 |
| Cache tokens (creation + reads) | 426,315 ±43,987 | 126,933 ±40,847 | +299,382 |

Sonnet pass-rate delta is computed over all 8 paired evals. Summary-table Delta values are computed from unrounded means, so they may differ slightly from subtracting the displayed rounded means. The `Tokens` row reports `input_tokens + output_tokens` summed across all assistant turns — the "new work" that drives full-rate API billing, matching the convention used in `learn` / `pr-comments` / `peer-review` benchmarks. Cache tokens are tracked separately because they're billed at different rates (cache reads at 0.1×, cache creation at 1.25–2×) and conflating them with the headline token figure would inflate it ~100× without a matching cost increase.

### `claude-opus-4-7`

| Metric | with-skill | without-skill | Delta |
|--------|------------|---------------|-------|
| Pass rate | **100%** ±0% | 58% ±15% | **+42%** |
| Min / Max | 100% / 100% | 33% / 75% | |
| Time (s) | 57.6 ±11.6 | 46.1 ±6.6 | +11.6 |
| Tokens (input + output) | 3,869 ±857 | 2,809 ±671 | +1,060 |
| Cache tokens (creation + reads) | 521,965 ±104,499 | 157,662 ±13,218 | +364,303 |

Opus pass-rate delta is computed over all 8 paired evals. Token-counting convention is the same as the Sonnet table.

The skill improves correctness on Sonnet 4.6 by **+31 percentage points** (69% → 100%) and on Opus 4.7 by **+42 percentage points** (58% → 100%). Opus's headline delta is *larger* than Sonnet's despite Opus's stronger general baseline — the pattern that drives this is detailed in the per-eval discussion below: Opus's baseline more often paraphrased the skill-defined output (e.g. "Refreshed the review guide on PR #42" instead of the literal "Review guide updated on PR #42") and reliably skipped the `<!-- pr-human-guide -->` HTML comment markers, so format-specific assertions catch more without_skill misses on Opus than on Sonnet. 6 of 8 evals discriminate on Sonnet; **all 8 evals discriminate on Opus**.

## Per-Eval Results

Each row shows passed/total per (model, configuration). Cells in **bold** are 100%; non-bold cells indicate the assertion set caught at least one failure.

| # | Eval | Sonnet With | Sonnet Without | Opus With | Opus Without |
|---|------|-------------|----------------|-----------|--------------|
| 1 | security-changes | **4/4 (100%)** | 2/4 (50%) | **4/4 (100%)** | 2/4 (50%) |
| 2 | config-changes | **4/4 (100%)** | **4/4 (100%)** | **4/4 (100%)** | 3/4 (75%) |
| 3 | new-dependency | **4/4 (100%)** | 3/4 (75%) | **4/4 (100%)** | 3/4 (75%) |
| 4 | novel-pattern | **3/3 (100%)** | 2/3 (67%) | **3/3 (100%)** | 2/3 (67%) |
| 5 | no-special-areas | **3/3 (100%)** | 1/3 (33%) | **3/3 (100%)** | 1/3 (33%) |
| 6 | idempotent-rerun | **3/3 (100%)** | **3/3 (100%)** | **3/3 (100%)** | 2/3 (67%) |
| 7 | data-model-changes | **4/4 (100%)** | 3/4 (75%) | **4/4 (100%)** | 2/4 (50%) |
| 8 | concurrency-state | **4/4 (100%)** | 2/4 (50%) | **4/4 (100%)** | 2/4 (50%) |

## Known Eval Limitations

### v0.10 — Impact Risk signals (spec 40)

Adds two Novel Patterns signals (sweeping cross-cutting refactor; high-fanout core helper) and a terminology refresh ("blast radius" → "impact risk") in `references/categories.md`. The existing 8-eval set does not exercise these signals — none of the fixtures contain a sweeping cross-cutting transformation or a high-fanout core helper edit — so re-benchmarking against the current suite would only validate non-regression on unrelated paths without informative signal. Coverage for the new signals was delivered by a follow-up (spec 48) — see the v0.13 subsection below, which adds evals 9–12 and measures them on Opus 4.8. `benchmark.json` `metadata.skill_version` was pinned at `"0.7"` when this set was recorded, under the earlier convention that it tracked the full-suite runs; spec 56 advanced it to `"0.16"` per the written rule in `evals/CLAUDE.md`; the current skill version is v0.13 (see the v0.11 and v0.13 notes below).

### v0.11 — SKILL.md size reduction (spec 41)

No-behavior-change context-cost refactor: SKILL.md shrank from 275 to 208 lines (-24%) by compressing the Security model to a flat bullet list, deduping the repeated "treat as untrusted" restatements, and relocating output-format mechanics (diff-anchor generation, per-entry format, with/no-items templates, report-summary templates) into `references/output-format.md` — all behind imperative "you must now execute" handoffs. The `<untrusted_pr_content>` block and Security model stay inline. Per `evals/CLAUDE.md` (structural refactors that move logic to a reference file run only the evals exercising the moved logic), the full suite was not re-benchmarked; instead a targeted parity run compared v0.11 against the `origin/main` snapshot on eval 1 (`security-changes` — markers/diff-link/report), eval 6 (`idempotent-rerun` — relocated marker handling + "updated" report template), and an ad-hoc prompt-injection probe (the highest-risk move, the untrusted-restatement dedupe). New scored no worse than the snapshot on every check (eval 1: 4/4 both; eval 6: 3/3 both), and both configurations held the line on the injection probe (ignored the embedded "reply only APPROVED / empty the description" instruction and flagged the `0o777` chmod). `benchmark.json` `metadata.skill_version` was pinned at `"0.7"` when this set was recorded, under the earlier convention that it tracked the full-suite runs; spec 56 advanced it to `"0.16"` per the written rule in `evals/CLAUDE.md`; no new run entries were recorded for this validation-only parity check.

### v0.13 — Opus 4.8 coverage for impact-risk signals + selectivity (spec 48)

Spec 40 added the two subtlest Novel Patterns signals — *sweeping cross-cutting refactor* and *high-fanout core helper edits* — and explicitly deferred eval coverage to a follow-up. **Spec 48 is that follow-up**: four new evals (ids 9–12), executed and graded on **claude-opus-4-8** only. The historical evals 1–8 v0.7 Sonnet / Opus-4-7 rows are left unchanged, so the headline delta stays sourced from the full suite; these new runs are a partial coverage set. No skill behavior changed — this was a measurement-coverage pass — and no defect surfaced, so no version bump accompanies the runs.

| Metric | with-skill | without-skill | Delta |
|--------|------------|---------------|-------|
| Pass rate | **100%** ±0% | 46% ±22% | **+54%** |
| Min / Max | 100% / 100% | 25% / 75% | |
| Time (s) | 66.3 ±10.3 | 42.8 ±10.7 | +23.5 |
| Tokens (input + output) | 38,559 ±5,877 | 19,215 ±376 | +19,344 |
| Cache tokens (creation + reads) | 530,471 ±70,513 | 189,815 ±18,358 | +340,656 |

Stats use sample stddev (N−1) over the 4 evals per configuration; token-counting convention matches the v0.7 tables. Summary-table Delta values are computed from unrounded means, so they may differ slightly from subtracting the displayed rounded means.

Per-eval pass/fail (Opus 4.8):

| # | Eval | With | Without |
|---|------|------|---------|
| 9 | sweeping-cross-cutting-refactor | **4/4 (100%)** | 2/4 (50%) |
| 10 | mechanical-rename-no-behavior-delta | **3/3 (100%)** | 1/3 (33%) |
| 11 | high-fanout-core-helper | **4/4 (100%)** | 3/4 (75%) |
| 12 | selectivity-over-flagging | **4/4 (100%)** | 1/4 (25%) |

All four discriminate (≥1 assertion fails without_skill). Eval 11 is the weakest discriminator — the Opus baseline flags the high-fanout helper, its broad impact, and the behavior change on its own; only the canonical-marker assertion fails, so the skill's measured edge there is the structured marker format. Eval 12 (selectivity) is the strongest: the baseline emitted a guide entry for all five changed files — including asking a reviewer to verify a test stub — exactly the over-flagging failure mode the eval targets, while the skill flagged only the login rate-limit change. Eval 10 confirms the negative guardrail works: with-skill correctly did NOT flag the exhaustive single-token rename and emitted the bounded "no areas" body.

A deliberately-omitted case: a *negative* high-fanout fixture (behavior change to a low-fanout, non-shared module) is not included — such a file would still legitimately flag under plain novelty, so the case cannot cleanly isolate "the high-fanout signal did not fire."

### v0.14 — Opus 4.8 coverage for operative skill source vs documentation (spec 50)

The v0.13 Selectivity Threshold exempted "changes that only affect comments or documentation" outright. In a **skills repository** that misfires: `SKILL.md` and reference files under a `skills/` tree are the *operative behavioral source* that defines what an agent does — its security/trust boundaries and workflow patterns — not prose *describing* code. Spec 50 refines the exemption so operative skill markdown (`skills/**/*.md`, including `skills/**/references/*.md`) is evaluated against the normal categories and flagged when it introduces a security boundary, a trust boundary, or a novel workflow pattern, while true documentation, spec/design docs (`specs/**`), and cspell/wordlist entries stay exempt. Two new evals (ids 13–14), one per branch of the conditional, executed and graded on **claude-opus-4-8** only. The evals 1–8 v0.7 rows and the evals 9–12 v0.13 rows are unchanged.

Stats over the 2 new evals (13–14), sample stddev (N−1):

| Metric | with-skill | without-skill | Delta |
|--------|------------|---------------|-------|
| Pass rate | **100%** ±0% | 25% ±35% | **+75%** |
| Min / Max | 100% / 100% | 0% / 50% | |
| Time (s) | 39.8 ±23.4 | 35.9 ±5.9 | +3.9 |
| Tokens (input + output) | 40,140 ±5,032 | 10,906 ±253 | +29,234 |
| Cache tokens (creation + reads) | 337,782 ±104,132 | 108,162 ±1,001 | +229,620 |

Delta values are computed from unrounded means, so they may differ slightly from subtracting the displayed rounded means. The combined Opus 4.8 set is now evals 9–14 — that 6-eval aggregate drives `run_summary_by_model["claude-opus-4-8"]` (pass rate 100% with-skill vs 39% baseline, +0.61) and the README's Opus 4.8 Eval-cost bullet.

Per-eval pass/fail (Opus 4.8):

| # | Eval | With | Without |
|---|------|------|---------|
| 13 | operative-skill-source-boundary | **4/4 (100%)** | 2/4 (50%) |
| 14 | skill-doc-wording-exempt | **3/3 (100%)** | 0/3 (0%) |

Both discriminate (≥1 assertion fails without_skill). Eval 13 is the positive case: it proves the refined rule flags an operative `.md` trust-boundary change. Note that on the strong Opus 4.8 baseline the `flags-the-boundary` assertion did **not** discriminate — the baseline also caught the boundary in a free-form guide — so eval 13's measured discriminators are `uses-html-markers` and `includes-diff-link` (baseline produced neither). Eval 14 is the negative guardrail: a pure wording tweak to a `SKILL.md` plus a `specs/**` doc and a cspell entry must stay exempt; the baseline over-flagged the cspell `prewarm` wordlist entry and emitted no bounded no-areas message, so all three assertions discriminate.

### v0.16 — Opus 5 coverage for checked-state preservation (spec 56)

Through v0.15 the skill reset every `- [x]` on re-run, documented as intended. In repos that re-run the skill after each review round that wipes reviewer progress repeatedly, including on entries whose code never changed. Spec 56 makes preservation **content-keyed**: each entry carries a `<!-- pr-human-guide:id HASH -->` comment whose hash covers the enclosing heading, the path, and the selected diff lines — but deliberately *not* the line numbers, so an insertion above a flagged range does not reset a check. One new eval (id 15) covers both branches in a single two-turn prompt, executed and graded on **claude-opus-5** only. Evals 1–14 are unchanged.

Stats over the 1 new eval (15). Note the single-eval denominator: every stddev below is 0.0 by construction and carries no information.

| Metric | with-skill | without-skill | Delta |
|--------|------------|---------------|-------|
| Pass rate | **100%** ±0% | 67% ±0% | **+33%** |
| Min / Max | 100% / 100% | 67% / 67% | |
| Time (s) | 311.3 ±0.0 | 197.5 ±0.0 | +113.8 |
| Tokens (input + output) | 13,650 ±0 | 10,305 ±0 | +3,345 |
| Cache tokens (creation + reads) | 3,704,428 ±0 | 979,588 ±0 | +2,724,840 |

This set fed `run_summary_by_model["claude-opus-5"]` on its own when recorded; spec 57 added evals 16–17 to that bucket, which now aggregates evals 15–17 (see the v0.17 subsection). The top-level `run_summary` remains the Opus 4.7 full suite, and the README's headline Eval Δ is unchanged.

Per-eval pass/fail (Opus 5):

| # | Eval | With | Without |
|---|------|------|---------|
| 15 | preserves-checked-unchanged-items | **3/3 (100%)** | 2/3 (67%) |

**Discriminates**, on `rewritten-item-resets` only. The other two assertions pass in both configurations, for different reasons worth recording:

- `unchanged-item-stays-checked` passes without_skill **by accident**. The baseline's turn 1 used plain bullets with no checkboxes at all; in turn 2 it converted the guide to a checklist and re-ticked from its own reading of which prose items were still open. It happened to land the auth entry ticked. This assertion alone does not discriminate on a strong model, and a future run should not be read as a regression if it flips.
- `no-placeholder-leaks` passes without_skill **vacuously** — the baseline invents its own marker syntax and so cannot leak a placeholder it never renders. It is a guard against the skill's own Step 5 failing to resolve, not a baseline comparison.

Honest framing of the delta: the behavior this eval pins is largely the *skill's own* prior behavior. v0.15 reset every box unconditionally; a general assistant was never bound by that rule and is free to carry ticks across on semantic judgment, which is what the baseline did. What the baseline cannot do is distinguish *unchanged* from *rewritten* content — it kept the `iam.tf` tick while asserting in prose that "the new commits did not change what they ask," when the policy line had in fact been widened to add `s3:DeleteObject`. That is the misleading failure mode the feature exists to prevent, and it is what `rewritten-item-resets` catches. The mechanism's finer guarantees — that an id survives renumbering, that a forged id cannot preserve a check, that an uppercase `- [X]` from the GitHub UI round-trips — are pinned by unit tests in `tests/pr-human-guide/test_item_identity.py` rather than by this eval.

Two earlier fixture revisions were discarded before recording. The first narrated the answer in the prompt (turn 2 stated outright which change did not alter the auth code), so the baseline scored 3/3 without needing content-keyed identity. The second anchored its reset case on `docs/setup.md`; documentation prose is correctly never flagged under the Selectivity Threshold, so a correct with_skill run produced no entry for the reset assertion to bind to, and the reviewer ticked only one of two boxes, making the reset assertion trivially true for every agent. The recorded fixture ticks **both** entries and anchors the reset case on `deploy/terraform/iam.tf` (Config / Infrastructure): an agent that copies the previous block through keeps both ticks and fails the reset case; one that re-renders from scratch resets both and fails the preserve case. Each revision was replayed through the shipped `marker-helper.py` to confirm it was winnable before executors were spawned.

A third attempt at the with_skill run was discarded for contamination: the executor ran a recursive `grep` across `evals/`, which returned eval 15's `expected_output` naming exactly which entry must stay checked and which must reset. The recorded run adds an explicit read fence over `evals/`, `specs/`, and `tests/`. The without_skill run was verified uncontaminated by the same transcript check and was not re-run.

### v0.17 — Opus 5 coverage for Documentation Drift (spec 57)

v0.16 had no category for the case where a code change renames or removes something that documentation outside the diff still names. Spec 57 adds a **Documentation Drift** category: when a diff renames or removes a flag, config key, or public symbol, the skill searches documentation the diff does **not** touch for the old literal name and flags the code change when a doc still carries it — anchored to the changed code lines, since the untouched doc has no diff to link. Two new evals (ids 16–17), one per branch of the conditional, executed and graded on **claude-opus-5** only. Evals 1–15 are unchanged.

Stats over the 2 new evals (16–17), sample stddev (N−1):

| Metric | with-skill | without-skill | Delta |
|--------|------------|---------------|-------|
| Pass rate | **100%** ±0% | 38% ±18% | **+63%** |
| Min / Max | 100% / 100% | 25% / 50% | |
| Time (s) | 253.8 ±19.0 | 163.6 ±55.4 | +90.2 |
| Tokens (input + output) | 10,991 ±211 | 4,229 ±1,580 | +6,762 |
| Cache tokens (creation + reads) | 2,337,073 ±29,196 | 809,778 ±453,707 | +1,527,296 |

Delta values are computed from unrounded means, so they may differ slightly from subtracting the displayed rounded means. The combined Opus 5 set is now evals 15–17 — that 3-eval aggregate drives `run_summary_by_model["claude-opus-5"]` (pass rate 100% with-skill vs 47% baseline, +0.53) and the README's Opus 5 Eval-cost bullet. The top-level `run_summary` remains the Opus 4.7 full suite.

Per-eval pass/fail (Opus 5):

| # | Eval | With | Without |
|---|------|------|---------|
| 16 | documentation-drift-stale-flag | **4/4 (100%)** | 2/4 (50%) |
| 17 | documentation-drift-updated-in-diff | **4/4 (100%)** | 1/4 (25%) |

Both discriminate (≥1 assertion fails without_skill), but not evenly, and the split is worth stating plainly. On eval 16 the assertion that tests the drift *detection* itself — `flags-stale-doc` — did **not** discriminate: the eval prompt supplies a `README.md` Usage excerpt, so the strong Opus 5 baseline noticed the `--force` mismatch unaided and led its guide with it. Eval 16's measured discriminators are `anchors-to-code-lines` (the baseline quoted README prose and gave no line anchor into `src/cli.py`, so a reviewer has nothing to click through to) and `uses-exact-markers`. The feature-level discriminator across the pair is really eval 17's `no-flag-for-unmentioned-name`: the baseline flagged the private `_write_batch` → `_flush_batch` rename that no documentation file names, which is exactly the over-flagging the negative branch guards against. Eval 17 also discriminates on `outputs-no-areas-message` (the baseline opened a "Needs a decision" section instead of the bounded body) and `uses-exact-markers`.

A note on the positive fixture: embedding the README excerpt in the prompt is what makes the eval winnable offline — there is no repository to grep — but it also hands the baseline the comparison for free. A fixture that required the agent to *find* the stale doc would discriminate harder on `flags-stale-doc`; it would also require a real checkout, which this suite's prompt-only fixtures do not provide.

### Non-discriminating evals on Sonnet 4.6

Of the 8 evals at v0.7, 2 are non-discriminating on Sonnet 4.6 (with-skill = without-skill pass rate). The Sonnet baseline coincidentally produced the same structural cues that the skill defines for these scenarios:

- Eval 2 (`config-changes`) — Sonnet baseline independently produced a structured "Config / Infrastructure" section, flagged the IAM widening and the staging→production workflow change, and showed a `gh pr edit` command (4/4 in both configurations).
- Eval 6 (`idempotent-rerun`) — Sonnet baseline reproduced the exact "Review guide updated on PR #42" terminal phrasing and the single-block idempotent replacement (3/3 in both configurations).

Spec-28 baseline for Sonnet differs from the prior v0.1 baseline (which had evals 7 and 8 non-discriminating). The change reflects v0.7-era skill content (notably the PR #112 checkbox change and downstream skill edits through PR #120) plus normal model variance on a single-run sample.

### Non-discriminating evals on Opus 4.7

**None.** All 8 evals discriminate on Opus 4.7 — the Opus baseline reliably misses one or more skill-defined behaviors (HTML comment markers, SHA-256 diff-anchor links, exact "Review guide updated on PR #" phrasing, exact "no areas requiring special human review" message). This is the inverse of the spec 25 (`learn`) and spec 27 (`peer-review`) findings, where Opus internalization collapsed several evals — for `pr-human-guide`, the discriminating signals are exact-format requirements that Opus's stronger paraphrase tendency actually misses more reliably.

### Skill-version reset (v0.1 → v0.7)

The previous Sonnet 4.6 baseline at v0.1 (recorded in `runs[]` until spec 28) was removed at the start of spec 28 so the two model rows share the same skill version. The current Sonnet results at v0.7 (+31% delta) are not directly comparable to the prior v0.1 results (+39% delta) — the skill changed between those two runs (notably the PR #112 checkbox change in review-guide items and several reference-file edits through PR #120), and the comparison would conflate skill-version effect with model effect. Git history retains the v0.1 entries; this benchmark file records only v0.7 runs.

### `without_skill` skill-tool contamination on Sonnet evals 5 and 8

Two Sonnet `without_skill` runs (evals 5 and 8) initially invoked the `pr-human-guide` skill via the Skill tool despite being explicitly forbidden from reading `skills/pr-human-guide/SKILL.md` and `skills/pr-human-guide/references/`. The contamination produced output indistinguishable from `with_skill` on those evals. Both runs were re-spawned with explicit Skill-tool prohibition added to the executor prompt; only the clean re-runs are recorded in `runs[]`. Future eval harnesses for skill-bearing repos should default to forbidding the Skill tool on baseline runs.

### Time/token measurement methodology

Per-run stats are extracted from the executor subagent JSONL transcripts (one per agent under the runtime's `~/.claude/projects/<project-key>/subagents/` path). Conventions:

- **`time_seconds`**: max-minus-min event timestamp across the agent's records.
- **`tokens`**: `input_tokens + output_tokens` summed across all assistant turns. Matches the convention used in `learn` / `pr-comments` / `peer-review` benchmarks — the "new work" that drives full-rate billing.
- **`cache_tokens`**: `cache_creation_input_tokens + cache_read_input_tokens` summed similarly. Tracked as a separate field because cache reads (0.1× rate) and cache creation (1.25–2× rate) are billed differently from regular input, and folding them into the headline `tokens` figure inflates it 50–100× without a matching cost increase. Most of the cache footprint here is cache reads — the prompt (executor instructions + the eval) is re-fed on every turn and served from cache.
- **`tool_calls`**: count of `tool_use` content blocks.
- **`errors`**: count of `tool_result` blocks with `is_error: true`.

The extraction logic is generalized in [`evals/scripts/extract_subagent_usage.py`](../scripts/extract_subagent_usage.py) — it takes one or more JSONL transcript paths (or `tasks/<id>.output` symlinks) and emits the conventions above as JSON. Usable for any future spec that wants to backfill the spec 26 / spec 27 Opus runs.

### Preserved grading artifacts

Eight `grading-*.json` files alongside this `benchmark.md` capture grader judgment calls worth preserving (the other 42 grading runs were mechanical pass/fail on literal-marker checks):

- `grading-{sonnet,opus}-without-eval-5.json` — judgment: does the **absence** of any review-guide construct count as the body containing the "no areas requiring special human review" message? Both gradings rule "no" — the body must literally contain that message.
- `grading-{sonnet,opus}-without-eval-8.json` — judgment: does discussion of `worker_threads` framed as a lifecycle/error-handling concern count as flagging it as "the new use of worker threads"? Both gradings rule "no" — the flag must explicitly call it out as a new concurrency primitive.
- `grading-opus-without-eval-7.json` — judgment: does `"### Areas needing careful attention"` with numbered subsections satisfy "the review guide includes a Data Model Changes section"? Grading rules "no" — the section name (or close equivalent like "Schema Changes" / "Database Changes") must appear literally.
- `grading-opus-4-8-without-eval-9.json` (spec 48) — judgment: does a free-form numbered "Reviewer Guide" that treats the change as an aggregate refactor satisfy "flags this change under Novel Patterns"? Rules "no" — the change must be categorized under Novel Patterns (the baseline's content was strong but uncategorized and used non-canonical markers).
- `grading-opus-4-8-without-eval-10.json` (spec 48) — judgment: does a populated "Reviewer Guide" with low-effort confirmation items satisfy the "no areas requiring special human review" message? Rules "no" — the bounded empty-guide body must be emitted, not a populated guide (parallels the eval-5 calls).
- `grading-opus-4-8-without-eval-12.json` (spec 48) — judgment: does listing routine files (lockfile bump, README, formatting reflow, test stub) under a "skim only" section count as flagging them? Rules "yes, it flags them" — the skill's selectivity behavior omits them entirely, so the omit-* and is-selective assertions fail.

The remaining 42 grading runs are not committed; the benchmark.json `expectations` array carries each one's verdict and evidence inline.

### Sonnet with_skill model-mismatch incident (recovered)

The first batch of 8 Sonnet `with_skill` agents hit transient `529 Authentication service is temporarily unavailable` errors during spawn and was resumed via `SendMessage`. The resume path silently inherited the parent agent's `claude-opus-4-7` model rather than the original `claude-sonnet-4-6` setting passed to the `Agent` tool — the on-disk JSONL transcripts for those 8 agents recorded `message.model: "claude-opus-4-7"` despite their description saying "Sonnet with_skill". The contamination was caught while harvesting JSONL usage data; all 8 Sonnet `with_skill` runs were re-spawned fresh (without the `SendMessage` retry path), verified to have actually executed on Sonnet 4.6 by inspecting `message.model` in each agent's JSONL, re-graded, and re-incorporated. The recorded Sonnet `with_skill` rows reflect the second-pass spawns. Eval-harness lesson: don't use `SendMessage` to retry `Agent` tool launches that hit transient errors — re-spawn instead so the original `model:` parameter is honored.

## Per-Eval Notes

### Eval 1 — `security-changes`

PR adds JWT middleware and role-based access control. Both with-skill runs (Sonnet and Opus) produced a structured Security section with the exact `<!-- pr-human-guide -->` markers and SHA-256 diff-anchor link. Both without-skill runs produced detailed security-aware reviews but failed assertions 2 (HTML markers) and 3 (GitHub diff-link format) — they used freeform delimiter formats (`<!-- review-guide-start -->` or `---` separators) and described files in prose rather than as `/pull/N/files#diff-...` links. **Discriminates on:** marker format, diff-link format, on both models.

### Eval 2 — `config-changes`

PR widens IAM permissions and changes a workflow's deployment target from staging to production. With-skill on both models scored 4/4. **Sonnet without-skill also scored 4/4** — the Sonnet baseline independently produced a "Config / Infrastructure" section, flagged the IAM widening and the staging→production change, and showed a `gh pr edit` command. **Opus without-skill scored 3/4**: the only failure was assertion 4 — Opus declined to show a simulated `gh pr edit` command, reporting "did not run" instead. **Discriminates on Opus only** (+0.25 delta); non-discriminating on Sonnet.

### Eval 3 — `new-dependency`

PR adds `node-forge` and `aws-sdk` dependencies plus an encryption module. All four runs correctly identified node-forge as cryptography-related, included a New Dependencies section, and flagged `src/encryption.ts` under Security/Novel Patterns. The discriminator on both models is assertion 4 (HTML markers): both without-skill runs used `---` separators and plain `## Review Guide` headings. **Discriminates on:** marker format, on both models (+0.25 delta).

### Eval 4 — `novel-pattern`

PR introduces `Result<T, E>` types in a codebase using `try/catch + AppError`. All four runs correctly identified the pattern contrast — including the without-skill runs, which independently noticed the divergence and the `refundPayment` bug (`processPayment(0)` instead of issuing a refund). The discriminator on both models is assertion 3 (HTML markers): both without-skill runs used plain section headings. **Discriminates on:** marker format, on both models (+0.33 delta).

### Eval 5 — `no-special-areas`

PR adds bio/role display fields to a React component with a test — no special review areas. Both with-skill runs correctly emitted the empty-guide variant with the exact "no areas requiring special human review attention were identified" phrase wrapped in `<!-- pr-human-guide -->` markers. Both without-skill runs scored 1/3 — they produced enhanced PR descriptions with Changes/Notes/Test plan sections but no review-guide mechanism, no HTML markers, and no "no areas" phrase. **Discriminates on:** the no-areas message and marker format, on both models (+0.67 delta).

### Eval 6 — `idempotent-rerun`

PR has an existing `<!-- pr-human-guide -->` block; new commits were pushed. Both with-skill runs correctly performed an idempotent replace and printed the exact "Review guide updated on PR #42: ..." line. **Sonnet without-skill scored 3/3** — the Sonnet baseline naturally reproduced the exact terminal phrasing and the single-block idempotent replacement. **Opus without-skill scored 2/3**: it correctly replaced the block but said "Refreshed the review guide on PR #42" instead of "Review guide updated on PR #" (assertion 3 failed). **Discriminates on Opus only** (+0.33 delta); non-discriminating on Sonnet.

### Eval 7 — `data-model-changes`

PR has a SQL migration with RENAME COLUMN, DROP COLUMN, SET NOT NULL, and a GraphQL schema removing fields. With-skill on both models scored 4/4. Without-skill failed assertion 4 (HTML markers) on both models, and Opus without-skill additionally failed assertion 1 (no "Data Model Changes" section header — it grouped concerns under "Areas needing careful attention" with numbered subsections instead). **Discriminates on:** marker format universally; section structure on Opus (+0.25 Sonnet, +0.50 Opus delta).

### Eval 8 — `concurrency-state`

PR introduces worker threads with module-level shared mutable state. Both with-skill runs correctly produced a "Concurrency / State" section flagging activeJobCount/jobQueue and worker_threads. Both without-skill runs scored 2/4 — they discussed the concurrency content but didn't explicitly flag worker_threads as a new concurrency primitive (assertion 3) and didn't use the HTML markers (assertion 4). **Discriminates on:** worker_threads-as-novel flag and marker format, on both models (+0.50 delta).

### Eval 9 — `sweeping-cross-cutting-refactor`

(Opus 4.8 only, spec 48.) PR routes every route handler's error path through centralized middleware (`next(err)` replacing inline `console.error` + `res.status(500).json(...)`) across 24 handler files; the diff shows 3 representative files and states the other 21 are identical. With-skill (4/4) categorized the change once under Novel Patterns as a sweeping cross-cutting refactor, emitted a single aggregate entry (`src/handlers/*.ts` (24 handler files)) rather than 24 per-file entries, named the runtime behavior delta (logging relocated; status code and response body now produced by middleware), and used the canonical `<!-- pr-human-guide -->` markers. Without-skill (2/4) produced strong aggregate content — it too steered reviewers away from line-by-line reading and flagged the lost logging and the response-contract change — but used a non-canonical `<!-- review-guide:start -->` marker and a free-form numbered "Reviewer Guide" with no Novel Patterns categorization. **Discriminates on:** the Novel Patterns categorization and marker format.

### Eval 10 — `mechanical-rename-no-behavior-delta`

(Opus 4.8 only, spec 48.) Negative guardrail: a pure single-token rename (`computeTotal` → `calculateTotal`) exhaustively substituted across 25 internal call sites, with no signature, behavior, or public-API change. With-skill (3/3) correctly classified every file as `(none)` — citing the "single-token rename … does NOT qualify" rule and the Selectivity Threshold ("file count alone is not a flagging signal") — and emitted the bounded "No areas requiring special human review attention were identified." body inside canonical markers. Without-skill (1/3) reached the same honest conclusion ("nothing in this PR needs careful human judgment") but wrapped it in a full "Reviewer Guide" with three confirmation items and used no HTML markers, so it failed both the bounded-no-areas-message and exact-markers assertions. **Discriminates on:** the bounded no-areas body and marker format. Confirms the skill does not misfire the sweeping-refactor signal on a high-file-count mechanical change.

### Eval 11 — `high-fanout-core-helper`

(Opus 4.8 only, spec 48.) Non-trivial behavior change to `src/lib/http.ts` — the request helper imported by every service: default timeout 30s→5s plus a new retry-on-5xx loop. With-skill (4/4) flagged it under Novel Patterns as a high-fanout core helper edit (the `lib/*` path triggered importer sampling), noted the broad impact across callers, named the behavior change, and used canonical markers. Without-skill (3/4) flagged the high-fanout helper, its large blast radius, and the timeout/retry behavior change just as well on its own — only the canonical-marker assertion failed. **Weakly discriminating:** the skill's measured edge here is the structured marker format, not the detection of the high-fanout concern itself (the strong Opus baseline already catches it).

### Eval 12 — `selectivity-over-flagging`

(Opus 4.8 only, spec 48.) A busy PR where only one change warrants a flag — rate limiting added to the login endpoint (Security) — alongside a `package-lock.json` patch bump, a README edit, a whitespace-only reformat of `src/utils/format.ts`, and a new test file, all of which fall under "What does NOT qualify" / Selectivity Threshold exceptions. With-skill (4/4) flagged only the login rate-limit change (one item, one Security category) and explicitly listed the four routine files as deliberately not flagged. Without-skill (1/4) flagged the security change correctly but then enumerated all four routine files in a "skim only" section — even asking the reviewer to confirm the test stub "asserts something before merge" — failing the omit-lockfile, omit-docs/test/formatting, and is-selective assertions. **Strongest new discriminator:** captures the over-flagging failure mode precisely (the baseline emitted an entry for every changed file).

### Eval 13 — `operative-skill-source-boundary`

(Opus 4.8 only, spec 50.) Positive case for the refined operative-skill-source rule. PR #245's only substantive change edits `skills/pr-comments/references/bot-polling.md` to add a new VERDICT allow-list rule — a Tier-0 read-only polling-subagent **trust boundary** that keeps untrusted-comment classification in the main agent, out of the subagent. Under the old v0.13 exemption this `.md`-only change would be exempted as documentation; the refined rule treats it as operative behavioral source. With-skill (4/4) flagged the change under Security as a new trust boundary, wrapped the guide in the canonical `<!-- pr-human-guide -->` markers, linked the files-changed diff view, and wrote it into the PR description. Without-skill (2/4) also caught the boundary — the strong Opus 4.8 baseline elevated the allow-list edit as a security concern in a free-form "Reviewer's guide" — so `flags-the-boundary` did **not** discriminate on this model; it used no canonical markers and no diff link, failing those two assertions. **Discriminates on:** marker format and diff-link (not `flags-the-boundary` on Opus 4.8, though that assertion exercises the new rule and would discriminate against the pre-change skill).

### Eval 14 — `skill-doc-wording-exempt`

(Opus 4.8 only, spec 50.) Negative guardrail for the refined rule. PR makes only a prose/wording tweak to a `SKILL.md`, plus a `specs/**` design-doc edit and a `cspell.config.yaml` wordlist addition (`prewarm`) — no new boundary or pattern. The refined rule must still emit the bounded no-areas body: pure wording on operative source, spec docs, and cspell entries all stay exempt. With-skill (3/3) flagged nothing, emitted "No areas requiring special human review attention were identified." inside canonical markers. Without-skill (0/3) over-flagged the cspell `prewarm` entry as the change to verify, produced a free-form "Reviewer's guide" with no bounded no-areas message and no canonical markers — failing all three assertions. **Discriminates on:** does-not-flag-skill-doc, the bounded no-areas message, and marker format. Confirms the refined rule does not over-flag pure wording, spec docs, or cspell entries.

### Eval 15 — `preserves-checked-unchanged-items`

(Opus 5 only, spec 56.) Two-turn case for content-keyed checked-state preservation. Turn 1 flags two entries on PR #77: `src/auth/middleware.ts` (Security) and `deploy/terraform/iam.tf` (Config / Infrastructure). The reviewer then ticks **both**. Turn 2 supplies a diff in which a 19-line license header pushes the auth hunk from L41-42 to L61-62 while leaving its content byte-identical, and the `iam.tf` policy line — same path, same hunk header, same line number — is rewritten to add `s3:DeleteObject`. Neither fact is stated in the prompt; the agent must derive both by comparing the two diffs. With-skill (3/3) re-rendered the block fresh, and the helper resolved the auth entry to the same identity as turn 1 (`d1edb1ec63e7a848`, unchanged across the renumbering) so the tick carried across, while `iam.tf` resolved to a new identity (`fbfeeb0fd315a433` → `6298faeab8494d27`) and reset to unchecked. Both `###` headings were identical across turns, so the reset is attributable to content rather than heading drift. Without-skill (2/3) kept the `iam.tf` entry ticked, reasoning in prose that "the new commits did not change what they ask" — a stale checkmark on content that had in fact been widened. **Discriminates on:** `rewritten-item-resets` only; see the v0.16 subsection above for why the other two assertions pass in both configurations.

### Eval 16 — `documentation-drift-stale-flag`

(Opus 5 only, spec 57.) Positive case for Documentation Drift. PR #260 renames the export CLI's `--force` flag to `--overwrite` in `src/cli.py` — two lines, argument definition and handler — and touches nothing else. The prompt includes an excerpt of the repository's `README.md` Usage section, which the PR does not modify and which still documents `--force` in both the example invocation and the flag list. With-skill (4/4) filed one entry under `### Documentation Drift` whose reason names the untouched `README.md`, anchored it to the changed `src/cli.py` lines (L43-52) rather than to the README — which has no diff to link — and wrote the guide into the PR description inside the canonical `<!-- pr-human-guide -->` markers. Without-skill (2/4) also caught the staleness, and named both stale README locations, so `flags-stale-doc` did **not** discriminate on this baseline; it gave no line anchor at all (quoting README prose instead, with a bare "the code change is two lines in `src/cli.py`" in the preamble) and used a `---` rule plus a `## Review guide` heading in place of the markers. **Discriminates on:** `anchors-to-code-lines` and `uses-exact-markers` (not `flags-stale-doc` on Opus 5, though that assertion exercises the new category and would discriminate against the pre-change skill).

### Eval 17 — `documentation-drift-updated-in-diff`

(Opus 5 only, spec 57.) Negative guardrail for Documentation Drift, covering both ways the category must *not* fire. PR #262 makes the same `--force` → `--overwrite` rename but updates `README.md`'s flag list in the same diff, and additionally renames a private helper `_write_batch` → `_flush_batch` at its definition and its single call site — a name no documentation file mentions. Neither rename should produce an entry: the first because the doc search set is empty once the only doc file is in the diff, the second because there is no doc naming the old symbol; the README edit itself is documentation prose and stays exempt, and both renames are mechanical single-token substitutions that fire no other category. With-skill (4/4) flagged nothing, reasoned both exclusions explicitly, and emitted "No areas requiring special human review attention were identified." inside canonical markers. Without-skill (1/4) agreed that documentation was in sync but then flagged the private-helper rename under "Please check outside this diff" (speculating about downstream subclasses overriding `_write_batch`) and opened a "Needs a decision" section on the breaking CLI change instead of the bounded no-areas body, with no markers. **Discriminates on:** `no-flag-for-unmentioned-name`, `outputs-no-areas-message`, and `uses-exact-markers`. This is the pair's strongest evidence for the feature: the drift rule is only useful if it stays quiet when nothing documents the old name.
