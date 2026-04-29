# pr-human-guide Benchmark Results

**Models tested**:
- `claude-sonnet-4-6` — full 8-eval suite × 2 configurations on 2026-04-28 (spec 28). Analyzer: **Sonnet 4.6**.
- `claude-opus-4-7` — full 8-eval suite × 2 configurations on 2026-04-28 (spec 28). Analyzer: **Sonnet 4.6** (chosen up front for analyzer-uniformity, following the spec 27 precedent).

**Evals**: 8 evals × 2 configurations × 2 models = **32 canonical runs**, all `run_number == 1`.

**Skill version**: v0.7. Both model rows produced under v0.7. The previous Sonnet runs at v0.1 (16 entries) were removed in spec 28 Phase 1 so both models share an apples-to-apples skill version; git history retains the prior shape.

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
| Time (s) | 57.6 ±11.6 | 46.1 ±6.6 | +11.55 |
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

Per-run stats are extracted from the executor subagent JSONL transcripts (one per agent under the runtime's `~/.claude/projects/.../subagents/` path). Conventions:

- **`time_seconds`**: max-minus-min event timestamp across the agent's records.
- **`tokens`**: `input_tokens + output_tokens` summed across all assistant turns. Matches the convention used in `learn` / `pr-comments` / `peer-review` benchmarks — the "new work" that drives full-rate billing.
- **`cache_tokens`**: `cache_creation_input_tokens + cache_read_input_tokens` summed similarly. Tracked as a separate field because cache reads (0.1× rate) and cache creation (1.25–2× rate) are billed differently from regular input, and folding them into the headline `tokens` figure inflates it 50–100× without a matching cost increase. Most of the cache footprint here is cache reads — the prompt (executor instructions + the eval) is re-fed on every turn and served from cache.
- **`tool_calls`**: count of `tool_use` content blocks.
- **`errors`**: count of `tool_result` blocks with `is_error: true`.

This closes the time/token measurement gap that the spec 26 and spec 27 Opus runs left open. The same JSONL-extraction approach is portable to those benchmarks if a future spec wants to retroactively backfill them.

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
