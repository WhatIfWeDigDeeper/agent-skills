# Spec 46: pr-comments — eval-driven review-and-improve pass (trim Step 13, hunt logic gaps, refresh benchmark)

Tracks issue
[#196](https://github.com/WhatIfWeDigDeeper/agent-skills/issues/196).

## Context

`skills/pr-comments/SKILL.md` is the most heavily-iterated skill in the repo.
This is an eval-driven review-and-improve pass: make targeted edits, then re-run
the 38-case eval suite (with-skill vs a fresh v-current snapshot baseline) to
confirm the edits help and to refresh the stale benchmark.

### Current reality (verified before writing this spec)

The issue (#196) was filed against a **stale snapshot** — it describes the skill
as "v1.45, 573 lines" with the Arguments/Step 13 prose still inline. Since then,
**PR #193 (`refactor(pr-comments): tighten SKILL.md and extract reference
files`)** already landed a tightening + reference-extraction pass. Verified
current state:

- `skills/pr-comments/SKILL.md` is **v1.46, 465 lines** (not v1.45 / 573).
- `references/` already holds 10 files, including `argument-parsing.md` (24
  lines, holds the `--auto`/`--max` deprecation + the `--auto 42` ambiguity) and
  `bot-polling.md` (320 lines, holds the polling/stale-HEAD machinery).
- `evals/pr-comments/` has **38 evals**; `benchmark.{json,md}` are recorded at
  **skill v1.36** (Opus 4.7 full-suite run dated 2026-04-24), so they trail the
  current v1.46 by ten patch versions.
- Opus 4.7 baseline (from `benchmark.json` run entries, not prose): with_skill
  mean pass-rate **0.9887**, without_skill **0.5986**, delta **+0.39**. Sonnet
  4.6 earlier run: with **1.0** / without **0.37**, delta **+0.63**.
- **9 of 38 evals are non-discriminating on Opus** (with ≤ without, both at
  ceiling 1.0): evals **5, 6, 24, 27, 29, 32, 33, 35, 38**. These are the "9
  Opus-non-discriminating evals" the issue asks to re-evaluate.

Because PR #193 already did most of the structural extraction, **two of the
issue's four areas are re-scoped below** — area 2 (Arguments density) is now
nearly complete and shrinks to a small dedup, while area 1 (Step 13 redundancy)
remains fully open. Areas 3 (logic-gap hunt) and 4 (benchmark refresh) apply as
written.

## Goals

1. **Trim Step 13 redundancy** — consolidate the repeated stale-HEAD reasoning.
2. **Finish Arguments dedup** — remove the one remaining duplication between
   SKILL.md and `argument-parsing.md` (most of this area is already done).
3. **Hunt logic gaps** — for each of five candidate gaps, decide *intentional
   exclusion* vs *genuine miss*, and fix only the genuine misses.
4. **Refresh benchmark** — re-run all 38 evals at v-current and bring
   `benchmark.{json,md}` from v1.36 up to current; re-evaluate the 9
   non-discriminating evals.

This is primarily a **prose-tightening + investigation** pass. Any behavioral
change must preserve everything asserted by `tests/pr-comments/`.

## Design

### Area 1 — Trim Step 13 redundancy (fully open)

The push/re-request flow (SKILL.md "### 13. Push and Re-request Review",
currently ~lines 355–415) restates the same fact —

> stale-HEAD bots are detected and merged in *after* the push, so the pre-push
> commenter list may be empty and the prompt/status-line must not imply it is
> final

— across **at least seven** locations: the lead-in paragraph (the sentence
containing "Bots that have previously reviewed this PR but haven't yet seen the
current HEAD are added after the push below"), the "Do not finalize the reviewer
list" paragraph, the manual-prompt paragraph (the sentence containing "The
`@user` list in this prompt is the pre-push commenter-derived set only"), the
auto-mode status-line paragraph (the sentence containing "stale-HEAD bots are
detected and merged in at step 2 below"), the no-commit status-line variant, the
empty-list variant (the sentence containing "When the pre-push commenter list is
empty"), and the numbered step-2 paragraph itself.

**Approach.** State the reasoning **once** as a single labeled invariant near the
top of Step 13, then have each prompt/status-line variant reference it instead of
re-deriving it. Candidate consolidation:

- Add one short invariant block at the top of Step 13, e.g. *"**Stale-HEAD
  invariant:** the pre-push commenter list is never final — stale-HEAD bots
  (including clean-approval-only bots) are detected and merged in at step 2,
  after any push. Every prompt/status-line below names the detection step rather
  than implying its `@user` list is complete; when that list is empty, drop the
  `from @user…` clause entirely."*
- Then collapse the per-variant restatements to the bare template + a pointer
  ("…per the stale-HEAD invariant above").
- Consider moving the **prompt/status-line templates themselves** (manual prompt,
  auto status line, their no-commit and empty-list variants) into
  `references/bot-polling.md` (which already owns the push-flow machinery) behind
  an imperative handoff, leaving SKILL.md with the invariant + the decision of
  which template to emit. Decide during implementation whether the move pays for
  itself or whether in-place collapse is cleaner; the templates are user-facing
  verbatim strings, so if moved they must follow the repo's fenced-` ```text `
  convention (per `skills/CLAUDE.md`).

**Constraint.** `tests/pr-comments/test_push_rerequest_routing.py` and
`test_stale_head_ordering.py` assert the ordering (stale-HEAD detection runs
*after* push) and the empty-list / no-commit branch behavior. The consolidated
text must keep every asserted branch reachable and worded so those tests still
pass. Re-read both test files before editing and after.

### Area 2 — Finish Arguments dedup (mostly done by PR #193)

`references/argument-parsing.md` already holds the full strip/precedence/
stickiness/validation rules, the `--auto N → --max N` deprecation note, and a
dedicated "`--auto` + PR-number disambiguation" section. The SKILL.md `##
Arguments` section (currently ~lines 24–44) is down to ~21 lines and already
delegates with "**you must now execute `references/argument-parsing.md`**".

The **one** remaining duplication: the disambiguation **table row**
`| `/pr-comments --auto 42` | auto | 42 (digit token read as the cap, **not** a
PR number — use `42 --auto`) |` in SKILL.md repeats the worked examples in
`argument-parsing.md` §"`--auto` + PR-number disambiguation". 

**Approach.** Keep the SKILL.md table rows that the tests assert and that
communicate the common cases; remove or shorten only genuinely duplicated
edge-case prose. Specifically, evaluate whether the `--auto 42` table row can be
dropped (its detail already lives in the reference) or reduced to a one-line "see
reference for `--auto` + PR-number disambiguation" pointer — **only if** no test
in `tests/pr-comments/test_pr_argument_parsing.py` /
`test_prcomments_argument_validation.py` depends on that row's presence. This is
a small change; do not re-extract what PR #193 already moved.

### Area 3 — Hunt logic gaps (investigation-first)

For **each** candidate below, the deliverable is a *decision* — intentional
exclusion (document it) or genuine miss (fix it) — backed by reading the current
SKILL.md + references. Do not pre-assume; confirm against the code.

| # | Candidate gap | Where to look | Likely (to confirm) |
|---|---------------|---------------|---------------------|
| a | **Edited/updated comment bodies across runs** — a reviewer edits a previously-replied comment to add a new request | Step 6 "previously-handled skip" (matches by reply presence + exact `login`) | Possible miss: a thread with an existing author/operator reply is skipped even if the body was edited after that reply |
| b | **Reaction-only feedback** (👍/👎, no text) | Steps 2/2b/2c fetch bodies, not reactions | Likely intentional exclusion — reactions carry no actionable request |
| c | **Resolved-then-reopened threads** | Step 3 discards `isResolved == true` | Likely already handled — a reopened thread reports `isResolved == false` and is picked up |
| d | **Comments on the PR description/body itself** | None of the 3 fetch sources read the PR body | Likely intentional — PR body is not a review comment |
| e | **Human comments arriving mid-run** | Step 6c repoll + `bot-polling.md` only re-check **bot** activity against `fetch_timestamp` | Genuine gap called out in the issue — a human comment posted after Step 2's fetch is not re-fetched within the same run |

**Output of this area:** a short findings note (in `tasks.md` and/or a comment on
#196) classifying each a–e. Then:

- For **intentional exclusions** (likely b, c, d): if the exclusion isn't already
  stated, add one line to SKILL.md "## Notes" or the relevant step documenting
  the boundary, so future reviewers don't re-flag it. No behavioral change.
- For **genuine misses** (candidate a and e): scope a minimal fix. For (a),
  consider augmenting the previously-handled-skip rule to re-open a thread whose
  comment `updated_at` is newer than the latest author/operator reply timestamp.
  For (e), consider widening the Step 6c / `bot-polling.md` repoll to re-fetch
  *all* comment sources (not just bot activity) against `fetch_timestamp`, or
  documenting it as an accepted limitation with a one-line note if a full fix
  risks loops. **Each genuine-miss fix needs a new test** in `tests/pr-comments/`
  and ideally a new eval; if a fix turns out to be large or risky, the
  conservative outcome is to document the limitation and defer the fix to a
  follow-up issue rather than over-build in this pass.

### Area 4 — Refresh benchmark

`benchmark.{json,md}` trail at v1.36; bring them to v-current using the
skill-creator eval loop.

1. **Snapshot the current skill as the baseline before editing** — copy the
   pre-edit `skills/pr-comments/` into a temp snapshot dir so the without-skill
   arm of later evals compares against today's skill, per the skill-creator
   protocol. (Record the exact version snapshotted.)
2. After areas 1–3 edits land, **re-run all 38 evals**, with_skill vs the
   snapshot baseline, on the same executor/analyzer models the benchmark
   documents (Opus 4.7 executor / Sonnet 4.6 analyzer for the headline run, to
   stay comparable; note model choice in the benchmark metadata).
3. **Re-evaluate the 9 non-discriminating evals** (5, 6, 24, 27, 29, 32, 33, 35,
   38). For each, decide: leave as-is (ceiling effect is acceptable coverage),
   strengthen the assertions so the skill's behavior is actually exercised, or
   note why it stays non-discriminating. Record the decision in `benchmark.md`.
4. **Update `benchmark.json` + `benchmark.md`** to the new version, run summary,
   and per-eval results. Follow the `evals/CLAUDE.md` benchmarking rules and the
   `benchmark.json` `\uXXXX`-escape handling note in the root CLAUDE.md (rewrite
   via `json.dump(..., ensure_ascii=True)`).

## Workflow / file changes

- `skills/pr-comments/SKILL.md` — Step 13 consolidation (area 1), Arguments
  table dedup (area 2), any logic-gap fixes + boundary notes (area 3), **one**
  `metadata.version` bump.
- `skills/pr-comments/references/bot-polling.md` — possibly receives the moved
  Step 13 prompt/status-line templates (area 1).
- `skills/pr-comments/references/argument-parsing.md` — only if area 2's dedup
  shifts text here (likely no change; it already holds the detail).
- `tests/pr-comments/` — new tests for any genuine-miss fix (area 3); update any
  test whose asserted wording the consolidation changes.
- `evals/pr-comments/benchmark.{json,md}` — refreshed to v-current (area 4);
  possibly strengthened assertions on some of the 9 non-discriminating evals.
- `evals/pr-comments/evals.json` — only if a logic-gap fix warrants a new eval.
- `README.md` — update the pr-comments row **only if** behavior changes.
- `evals/security/pr-comments.baseline.json` — refresh **only if** an ingestion
  path changes (run `bash evals/security/scan.sh --update-baselines --confirm`).

## Constraints

- **Preserve behavior asserted by `tests/pr-comments/`**: argument parsing,
  comment classification, bot-poll routing, stale-HEAD ordering, post-edit drift,
  consistency check, convention sanity-check, timeline comments. Run
  `uv run --with pytest pytest tests/pr-comments/` before and after; run the full
  `tests/` suite at the end (lift sandbox restrictions — in Claude Code,
  `dangerouslyDisableSandbox: true` — per the uv-cache note in CLAUDE.md).
- **Keep workflow instructions assistant-neutral** (portability section of
  CLAUDE.md) — no brand-specific strings; Claude Code mechanics noted as
  qualifiers.
- **Bump `metadata.version` exactly once** for the whole PR (run the
  `git diff origin/main … rg '^\+  version:'` check before committing any
  SKILL.md change).
- **Use phrase anchors, not line numbers**, when `tasks.md` references locations —
  the file shifts as edits land.
- Verify each "Step N" reference in this spec against the current SKILL.md before
  acting; step numbers drift.

## Verification

1. `uv run --with pytest pytest tests/pr-comments/` — all pass (existing + new).
2. `uv run --with pytest pytest tests/` — no regressions across suites.
3. Re-read SKILL.md end-to-end — Step 13 reads cleanly, no dangling
   cross-references, the stale-HEAD invariant is stated once and referenced.
4. `npx cspell skills/pr-comments/SKILL.md skills/pr-comments/references/*.md
   specs/46-pr-comments-eval-driven-review/*.md` — add any new words to
   `cspell.config.yaml` (alphabetically sorted).
5. Benchmark: with_skill mean pass-rate ≥ the recorded v1.36 baseline (0.9887 on
   Opus); no eval regresses below its prior with_skill rate without an explained
   cause. delta vs the v-current snapshot baseline recorded in `benchmark.md`.
6. `git fetch origin && git diff origin/main -- skills/pr-comments/SKILL.md |
   rg '^\+  version:'` — exactly one bump.
7. If any ingestion path changed: `bash evals/security/scan.sh --confirm` clean
   against the (refreshed) baseline.
