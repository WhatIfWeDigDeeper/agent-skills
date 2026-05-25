# Spec 40: pr-human-guide — Impact Risk signals (augment existing categories)

## Context

A Gemini review of the `pr-human-guide` skill recommended adding a 7th
category, "Blast Radius / Operational Impact", to capture high-volume file
changes, modification of core critical modules, and sweeping refactors. The
suggestion has real motivation — those cases are reviewer-relevant — but the
existing six categories already encode much of the concept (Config /
Infrastructure explicitly mentions impact that isn't visible from the diff;
Data Model covers schema-level impact; Novel Patterns can absorb sweeping
changes), and adding a 7th category broadens flagging in a way that risks
false positives on mechanical churn (auto-formatting, dep bumps, exhaustive
renames) — exactly the noise the skill's Selectivity Threshold is designed
to suppress.

The chosen direction is to **augment existing categories** rather than add
a 7th, and to use the term **"Impact Risk"** instead of "blast radius"
throughout for tone (less violent metaphor, same meaning). Two genuine gaps
are added under **Novel Patterns**:

1. **Sweeping cross-cutting refactor** — a mechanical change applied across
   many files at once where the reviewer's decision is about the whole
   transformation, not each line.
2. **High-fanout core helper edits** — non-trivial behavior changes to a
   centrally-imported module (root router, base controller, shared error
   helper, central middleware) where one small change has outsized reach.

A guardrail clause is added to make the false-positive risk explicit: file
count alone is not a flagging signal, and pure mechanical changes (formatting,
dep-version bumps, single-token exhaustive renames) do not qualify even when
they touch many files.

Section 5 (Novel Patterns) currently frames itself around *novelty* —
introducing a pattern the codebase hasn't seen. The new signals are about
*aggregate scope* and *fanout*, which is a conceptual stretch of Section 5
rather than a perfect fit. Adding a 7th category would have been
conceptually cleaner; we chose the stretch in exchange for keeping the
six-category surface stable and avoiding new benchmark churn. Edit B
includes a short rationale paragraph documenting this trade-off so the
section's framing stays coherent for future editors.

## Design

### Edit A — terminology refresh: "blast radius" → "impact risk"

In `skills/pr-human-guide/references/categories.md`, replace both literal
occurrences:

- Section **2. Config / Infrastructure**, "Why human review is needed"
  paragraph: `"a blast radius that isn't visible from the diff alone"` →
  `"impact risk that isn't visible from the diff alone"` (threads the
  new term through the prose rather than leaving "have impact"
  ungrammatical).
- Section **4. Data Model Changes**, "What does NOT qualify" list: `"low
  blast radius"` → `"low impact risk"`.

Do **not** modify `evals/pr-human-guide/benchmark.json` — the existing
`"consider blast radius if credentials are compromised"` string is recorded
model output (verbatim transcript evidence), not skill-authored prose.
Modifying it would falsify the historical record. The
`specs/22-pr-human-guide/plan.md` reference is also historical and is left
alone.

### Edit B — augment Novel Patterns with two Impact Risk signals

Section 5's existing framing focuses on novelty (introducing a new pattern
the codebase hasn't seen). The two new bullets extend that framing to cover
transformations whose reviewer-relevant decision is about **aggregate scope
or fanout** rather than per-line correctness — the reviewer still has to
make a judgment call about the change as a whole, which is the underlying
purpose Section 5 serves. This conceptual stretch is acknowledged here so
future editors don't accidentally narrow the section back to novelty-only.

In `skills/pr-human-guide/references/categories.md`, section **5. Novel
Patterns**, add to the "Examples of novel patterns that qualify" list.
The two new bullets intentionally use a `**Label** — explanation` style
(unlike the existing sentence-form bullets in this section) so the new
signals have named handles reviewers can reference; this stylistic
divergence is deliberate and not a sync mistake:

- **Sweeping cross-cutting refactor** — a transformation applied across
  many files at once where the change carries a behavior or contract delta
  (e.g., a framework migration across an entire module, an API surface
  change propagated to 20+ call sites, swapping a logging or error-handling
  pattern in a way that changes runtime behavior). Flag for the aggregate
  decision, not each file; the question for the reviewer is "is this the
  right transformation," not "is each line correct." Pure-mechanical
  renames with no semantic delta do **not** qualify — see Edit C.
- **High-fanout core helper edits** — non-trivial behavior changes to a
  module that is imported broadly across the codebase (root router, base
  controller, shared error helper, central middleware chain). **Trigger
  sampling** when (a) the changed file's path matches a typically-shared
  layout (`router`, `controller`, `middleware`, base error/exception
  classes, `lib/*`, `util/*`, `common/*`) **or** (b) the changed export
  name appears as an import in 5+ other files within the same PR diff;
  otherwise skip sampling. When sampling fires, read 2–3 importers and
  check whether the changed function/export is called from many call
  sites.

### Edit C — add a "does NOT qualify" guardrail to Novel Patterns

In the same section's "What does NOT qualify" list, add:

- Pure mechanical changes with no behavior delta (auto-formatting,
  whitespace-only diffs, dependency-version bumps in lockfiles, single-token
  renames where the new name is exhaustively substituted) — count as routine
  even when they touch many files.

### Edit D — reinforce the Selectivity Threshold with a file-count clause

In the **Selectivity Threshold** section near the bottom of `categories.md`,
append one sentence to the **first paragraph** (the one ending in *"…flag
only when there is a concrete reviewer-relevant risk or uncertainty."* —
not the "Exceptions" list that follows):

> File count alone is not a flagging signal — flag a sweeping change only
> when the reviewer has a meaningful yes/no decision to make about the
> transformation as a whole.

### Edit E — version bump

Bump `metadata.version` in `skills/pr-human-guide/SKILL.md` from `"0.9"` to
`"0.10"`. Before editing, check whether the active branch already contains a
version bump relative to `origin/main`:

```bash
git fetch origin && git diff origin/main -- skills/pr-human-guide/SKILL.md | rg '^\+  version:'
git diff --name-status origin/main...HEAD -- skills/pr-human-guide/SKILL.md
```

If a bump already exists on the branch, do not bump again (once-per-PR rule).
If `SKILL.md` is new in the PR, the new-skill exception applies and no bump
is required; that exception is not expected here.

## Tests

No new tests are required. The existing `tests/pr-human-guide/` suite covers
argument validation, diff-anchor formatting, guide placement (marker-helper),
help detection, report format, and prompt-injection handling. None test
classification content or category text, so the changes in this spec do not
require test changes. Run the existing suite as a regression check during
Phase 4 verification.

## Evals

Do **not** add a new eval and do **not** re-run the existing 8-eval suite in
this spec. The existing evals are small focused fixtures — none would trigger
the new sweeping-refactor or high-fanout signals, so re-running them would
validate non-regression on unrelated paths at meaningful cost without
informative signal.

Document the decision explicitly in `evals/pr-human-guide/benchmark.md` as
a single note added near the existing "Known Eval Limitations" section:

> **v0.10 — Impact Risk signals (spec 40).** Adds two Novel Patterns signals
> (sweeping cross-cutting refactor; high-fanout core helper) and a
> terminology refresh ("blast radius" → "impact risk"). The existing eval
> set does not exercise these signals, so re-benchmarking would not be
> informative. Coverage for the new signals is a follow-up spec with new
> fixtures.

If a future spec wants coverage for the new signals, recommended fixtures:
- A PR that swaps a logging or error-handling pattern across 25 files
  where the new pattern changes runtime behavior (e.g., from
  `throw new Error(...)` to a Result-type return) — exercises the
  Sweeping cross-cutting refactor signal because the reviewer has to
  decide whether the transformation is correct in aggregate, not per
  line.
- A negative fixture: a pure mechanical single-token rename
  (`oldName` → `newName`) exhaustively substituted across 25 internal
  call sites, no public-API or behavior change — exercises Edit C's
  guardrail (must NOT trigger the Sweeping refactor signal).
- A small one-line behavior change to a root-imported helper (e.g.,
  `src/lib/router.ts` used in 30 files) — exercises the High-fanout
  core helper signal; the agent should fire its trigger heuristic
  because the file path matches the shared-layout list.

## Files to Modify

| File | Change |
|---|---|
| `skills/pr-human-guide/references/categories.md` | Edits A–D: terminology refresh, two new Novel Patterns signals, one new "does NOT qualify" clause, one Selectivity Threshold sentence. |
| `skills/pr-human-guide/SKILL.md` | Edit E: bump `metadata.version` from `"0.9"` to `"0.10"`. |
| `evals/pr-human-guide/benchmark.md` | Add one note documenting the no-re-benchmark decision for v0.10. |
| `cspell.config.yaml` | Add any new terms surfaced by cspell (likely candidate: `codemod`), alphabetically sorted. |

No changes are expected in:
- `evals/pr-human-guide/benchmark.json` (no run data changes; `metadata.skill_version` stays at `"0.7"` per the existing convention that the field reflects the version of recorded runs, not the current skill version — already documented in `benchmark.md`).
- `evals/pr-human-guide/evals.json` (no new eval).
- `README.md` (six-category list is unchanged; Eval Δ and Eval cost bullet remain valid since no benchmark numbers change).
- Any `CLAUDE.md` file or `.github/copilot-instructions.md` (the changes are skill content, not project rules — no sync required).
- `tests/pr-human-guide/` (no behavior change to argument parsing, marker handling, report format).

## Verification

1. `rg -n 'blast radius' skills/pr-human-guide/` returns no results.
2. `rg -n 'impact risk|impact that isn'"'"'t' skills/pr-human-guide/references/categories.md` returns the two replacements.
3. `rg -n 'Sweeping cross-cutting refactor|High-fanout core helper' skills/pr-human-guide/references/categories.md` returns the two new bullets.
4. `rg -n 'Pure mechanical changes with no behavior delta' skills/pr-human-guide/references/categories.md` returns the new "does NOT qualify" bullet.
5. `rg -n 'File count alone is not a flagging signal' skills/pr-human-guide/references/categories.md` returns the new Selectivity Threshold sentence.
6. `rg -n '^  version:' skills/pr-human-guide/SKILL.md` shows `version: "0.10"`.
7. `rg -n 'v0.10 — Impact Risk signals' evals/pr-human-guide/benchmark.md` shows the no-re-benchmark note.
8. `uv run --with pytest pytest tests/pr-human-guide/ -v` passes.
9. `uv run --with pytest pytest tests/` passes.
10. `npx cspell skills/pr-human-guide/references/categories.md skills/pr-human-guide/SKILL.md evals/pr-human-guide/benchmark.md specs/40-pr-human-guide-impact-risk-signals/*.md` is clean.
11. Re-read `categories.md` end-to-end to confirm tone and selectivity remain consistent — no contradiction between the new sweeping-refactor signal and the existing "What does NOT qualify" lists in other categories.
12. Re-read both modified spec files (`plan.md`, `tasks.md`) before reporting done — catches consistency gaps yourself rather than leaving them for the next review round.

## Branch

`spec-40-pr-human-guide-impact-risk-signals`

## Peer Review

Peer-review tasks in this spec use the local `claude` CLI directly, not
`/peer-review`. Always pass `-p` for non-interactive mode. Example:

```bash
claude -p "review staged files"
```

The command can take several minutes to complete.

### Phase 0 — pre-spec consistency pass

Before implementation edits, stage only `specs/40-pr-human-guide-impact-risk-signals/plan.md` and `tasks.md`, then run:

```bash
claude -p "review staged files"
```

Apply valid findings, record a per-iteration summary in `tasks.md`, and re-run until zero valid findings or iteration cap 2. If implementation has already begun before Phase 0 runs, record that deviation in `tasks.md`, do not retroactively claim the pre-spec review happened on time, and rely on the pre-ship branch pass as the required fresh-context review.

### Pre-ship branch pass

After implementation and verification, stage the full branch diff and run:

```bash
claude -p "review staged files"
```

Apply valid findings, record summaries in `tasks.md`, and re-run until zero valid findings or iteration cap 4.

## Risks

- **Over-flagging on sweeping refactors.** The new "Sweeping cross-cutting refactor" signal could produce false positives on benign mechanical churn. Mitigation: Edit C (the "does NOT qualify" guardrail) and Edit D (the Selectivity Threshold sentence) explicitly exclude formatting, dep-bumps, and exhaustive renames. If a real-world PR review surfaces false positives after merge, tighten the signal in a follow-up rather than removing it.
- **Detection cost for high-fanout core helpers.** Sampling 2–3 importers adds tool calls on PRs that touch shared modules. The cost is bounded by Edit B's explicit trigger heuristic — sampling fires only when the changed file's path matches a typically-shared layout (`router`, `controller`, `middleware`, base error classes, `lib/*`, `util/*`, `common/*`) **or** when the changed export appears as an import in 5+ other files in the same diff. Without that gate the signal would either silently skip every PR or sample on every PR; the heuristic gives the agent a concrete operational rule.
- **No new eval coverage for the new signals.** Documented explicitly in `benchmark.md`. If a follow-up spec adds the recommended fixtures, the v0.10 baseline can be characterized retroactively.
- **Version-bump discipline.** Only bump once per PR. Phase 1.1 verifies no prior bump exists on the branch.
- **Terminology drift.** Other files in the repo may use "blast radius" idiomatically (e.g., `skills/uv-deps/SKILL.md`). Those uses are unrelated to PR review scoring and are intentionally left alone — the terminology change is scoped to `pr-human-guide` content only.

## Shipping

1. Create branch `spec-40-pr-human-guide-impact-risk-signals`.
2. Complete Phase 0 peer review of the spec docs using `claude -p "review staged files"`.
3. Implement Edits A–E.
4. Add the `benchmark.md` no-re-benchmark note.
5. Run verification.
6. Run the pre-ship peer review using `claude -p "review staged files"`.
7. Commit, push, and open a PR.
8. Run `/pr-comments {pr_number}` after pushing per repo convention.
9. Run `/pr-human-guide` before human review.
10. Merge only after CI is green and a human has reviewed.
