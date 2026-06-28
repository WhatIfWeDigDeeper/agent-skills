# Spec 48 — pr-human-guide eval coverage for impact-risk signals + selectivity

## Context

`pr-human-guide` is at **v0.13**. Mechanically it is in excellent shape (135
passing unit tests, 100% with-skill pass rate, strong security model). The gap is
in **eval coverage**, not instructions:

1. **Two detection signals have zero eval coverage.** Spec 40 (v0.10) added the
   two subtlest Novel Patterns signals — *sweeping cross-cutting refactor* and
   *high-fanout core helper edits* — and explicitly deferred their coverage:
   > "Coverage for the new signals is a follow-up spec with new fixtures."
   Spec 40's plan even lists recommended fixtures (`specs/40-…/plan.md`, "Evals"
   section). **This spec is that follow-up.** These signals are the most
   judgment-heavy and misfire-prone in the skill, yet are unmeasured.
2. **No selectivity / over-flagging eval.** Every existing positive eval is a
   clean "here is a category, flag it" case. Nothing tests the Selectivity
   Threshold. For a skill whose value is *"where should attention go,"* the
   failure mode that destroys it is flagging *everything* — currently unmeasured.
3. **Stale benchmark.** Recorded runs are at skill **v0.7** on retired models
   (Sonnet 4.6 / Opus 4.7), single-run. Current model is **Opus 4.8**.

**Intended outcome:** four new evals (two positive signal probes, one negative
guardrail probe, one selectivity probe), executed and graded on Opus 4.8, with
`benchmark.json` / `benchmark.md` / `README.md` updated. No skill behavior change
is planned — this is a measurement-coverage pass. If an eval reveals a skill
defect, it is surfaced for a separate follow-up (which would carry the version
bump); this spec does not edit SKILL.md or its references.

## Scope decisions (confirmed with the user)

- **4 new evals** (ids 9–12) — covers both branches of each new conditional per
  `evals/CLAUDE.md` ("For conditional rules… add an eval for each branch").
- **New evals only on Opus 4.8** — keep the historical v0.7 Sonnet/Opus rows
  unchanged; add the new runs as a distinct, clearly-versioned set. The headline
  delta stays sourced from the historical full suite; the new runs are documented
  as a v0.13/Opus-4.8 coverage addition.

## Eval designs

All four follow the established `evals/pr-human-guide/evals.json` pattern: the
fixture is embedded inline in `prompt`; the prompt reads as a natural user
request and **never names the skill** (skill-name leakage collapses the baseline
— see `evals/CLAUDE.md`); assertions are `{id, text}` testing **user-facing
output**. Because the fixtures reference fake PRs, executors **simulate** the
`gh pr edit`/`gh pr view`/`gh pr diff` calls (echo the command and the body that
would be posted) — matching how the existing 8 fixtures are non-live.

The full prompt/assertion text for each eval is the authoritative content the
implementer inserts verbatim; it lives in `tasks.md` (Task 1) so the JSON can be
copied directly. Summaries:

### Eval 9 — `sweeping-cross-cutting-refactor` (positive)

Maps to spec 40 recommended fixture #1. PR routes every route handler's error
path through centralized middleware (`next(err)` replacing inline
`console.error` + `res.status(500).json(...)`) across **24 handler files**; the
diff shows 3 representative files and states the other 21 are identical. The
reviewer-relevant decision is aggregate ("is this the right transformation"), and
there is a real **behavior/contract delta** (error responses + logging now
produced centrally instead of per-handler).

Assertions: `flags-as-novel-pattern` · `flags-aggregate-not-per-file` ·
`notes-behavior-delta` · `uses-html-markers`.

### Eval 10 — `mechanical-rename-no-behavior-delta` (negative)

Maps to spec 40 recommended fixture #2. Pure single-token rename
(`computeTotal` → `calculateTotal`) exhaustively substituted across **25 internal
call sites**; no signature, behavior, or public-API change. Per
`references/categories.md` ("What does NOT qualify": "single-token renames where
the new name is exhaustively substituted") and the Selectivity Threshold ("File
count alone is not a flagging signal"), this must **not** trigger the
sweeping-refactor signal — nothing should be flagged, so the bounded "no areas"
empty-guide variant is expected.

Assertions: `does-not-flag-rename` · `outputs-no-areas-message` ·
`uses-exact-markers`.

### Eval 11 — `high-fanout-core-helper` (positive)

Maps to spec 40 recommended fixture #3. Non-trivial behavior change to
`src/lib/http.ts` — the request helper imported by every service: default timeout
30s→5s plus a new retry-on-5xx loop. The path matches the shared-layout trigger
list (`lib/*`), so the High-fanout core helper sampling heuristic should fire.
The reviewer concern is the broad impact across callers, not the single file.

Assertions: `flags-high-fanout-helper` · `notes-broad-impact` ·
`flags-behavior-change` · `uses-html-markers`.

### Eval 12 — `selectivity-over-flagging`

A busy PR where only one change warrants a flag: rate limiting added to the login
endpoint (Security). It also touches a `package-lock.json` patch version bump, a
`README.md` edit, a whitespace-only reformat of `src/utils/format.ts`, and a new
test file — all of which fall under "What does NOT qualify" / the Selectivity
Threshold exceptions and must **not** be flagged.

Assertions: `flags-security-change` · `omits-lockfile-bump` ·
`omits-docs-test-and-formatting` · `is-selective`.

### Deliberately out of scope

A **negative high-fanout** fixture (behavior change to a low-fanout, non-shared
module) is omitted: such a file would still legitimately flag under plain
novelty/other categories, so the case cannot cleanly isolate "the high-fanout
signal did not fire." Documented here so a future editor does not read its
absence as an oversight.

## Acceptance criteria for discrimination

Per `evals/CLAUDE.md`, each new eval must have **at least one assertion that fails
without_skill** — per-eval discrimination, not "some discriminate." The negative
evals (10, and the omit-* assertions of 12) discriminate on the baseline's
tendency to over-explain / list every file and to skip the canonical markers and
the bounded "no areas" body.

## Benchmark recording approach

- Add **8 new run entries** (4 evals × 2 configs) to `evals/pr-human-guide/benchmark.json`
  `runs[]`, each tagged with the executor model `claude-opus-4-8` and a
  `run_number`. Each gets `eval_name`, `pass_rate`, `passed`, `failed`, `total`,
  and `expectations` (`{text, passed, evidence}` only), plus `time_seconds` /
  `tokens` / `cache_tokens` / `tool_calls` / `errors` (use `null` for any
  unrecorded measurement, never `0`).
- Do **not** mutate the 32 historical v0.7 runs or their `run_summary`. Add the
  new set under a clearly labeled structure (a separate summary block keyed to
  Opus 4.8 + a top-level `notes` entry naming the model and skill version).
  `metadata.skill_version` stays `"0.7"` per the existing convention that the
  field reflects the version of the *recorded full-suite* runs (already
  documented in `benchmark.md`); the new partial set is version-noted in prose.
  `metadata.evals_run` is extended to include 9–12.
- `run_summary` stats for the new set use sample stddev (N−1); `delta` values are
  signed strings at 2-decimal precision for pass_rate, computed from unrounded
  means.

## benchmark.md updates

- Add a `### v0.13 — Opus 4.8 coverage for impact-risk signals + selectivity
  (spec 48)` subsection under "Known Eval Limitations" describing the four new
  evals, the new-evals-only-on-4.8 decision, and the selectivity finding.
- Add a per-eval `### Eval N — \`name\`` section for each of 9–12.
- Update the token-count denominator sentence ("N of M") to the new totals.

## README updates

- Update the `Eval cost` bullet in the pr-human-guide Skill Notes section to note
  the v0.13 coverage expansion and the Opus 4.8 run (4 new evals, selectivity +
  impact-risk signals). The historical headline delta (`+31% Sonnet 4.6 / +42%
  Opus 4.7`) stays as the table's `Eval Δ` unless the new runs change the
  full-suite headline — they do not, since the new runs are a separate partial
  set.

## Files to modify

| File | Change |
|---|---|
| `evals/pr-human-guide/evals.json` | Add evals 9–12 (verbatim content in tasks.md Task 1). |
| `evals/pr-human-guide/benchmark.json` | Add 8 Opus 4.8 run entries + new summary block + `notes` entry; extend `metadata.evals_run`. |
| `evals/pr-human-guide/benchmark.md` | Add coverage subsection + 4 per-eval sections; update denominator sentence. |
| `evals/pr-human-guide/workspace/iteration-2/…` | New run outputs + grading + timing (commit grading json selectively per `evals/CLAUDE.md`; no raw transcripts). |
| `README.md` | Update pr-human-guide `Eval cost` bullet. |
| `cspell.config.yaml` | Add any new terms surfaced by cspell, alphabetically sorted. |

**No changes** to `skills/pr-human-guide/SKILL.md` or its references (no behavior
change → no version bump), and **no** `CLAUDE.md` / `.github/copilot-instructions.md`
changes (eval content, not project rules). Exception: if execution reveals a
skill defect, stop and surface it — a fix is a separate spec/PR with its own bump.

## Verification

- `python3 -c 'import json; json.load(open("evals/pr-human-guide/evals.json"))'`
- `python3 -c 'import json; json.load(open("evals/pr-human-guide/benchmark.json"))'`
- Expectation key schema: `jq '[.runs[] | .expectations[]? | select((.|keys) != ["evidence","passed","text"])] | length'` on benchmark.json returns `0`.
- `uv run --with pytest pytest tests/pr-human-guide/` (lift sandbox) stays **135
  green** — no skill-logic change expected.
- `npx cspell evals/pr-human-guide/*.md specs/48-pr-human-guide-eval-coverage/*.md`
- Each new eval discriminates: at least one assertion fails without_skill.
- Launch the eval viewer (`generate_review.py`, iteration-2) so outputs are
  reviewable before finalizing.
