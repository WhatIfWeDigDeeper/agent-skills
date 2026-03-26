# Spec 10: pr-comments — Slim down SKILL.md

## Problem

`skills/pr-comments/SKILL.md` is 569 lines (v1.11), exceeding the 500-line guideline. Each feature version added necessary logic but also accumulated verbosity and duplication between inline steps and the Notes section. The file is getting hard to scan.

## Proposed Change

Extract reference material into new/existing reference files and prune duplicated prose from the Notes section. No behavior changes — identical workflow, same steps in same order, same decision logic. Version bumped to 1.12 per CLAUDE.md (documentation changes require a version bump).

## Detailed Changes

### 1. Extract Step 14 report templates → new `references/report-templates.md` (~60 lines)

Move the entire template block (standard report template, auto-loop summary table, exit reason values) into a new reference file. Replace Step 14 body with:

```markdown
### 14. Report

Generate the final report using the templates in `references/report-templates.md`. Omit lines that don't apply. In auto-loop mode, use the auto-loop summary table instead of the standard report; include the deferred follow-up-issue offer if there were out-of-scope declines.
```

`references/report-templates.md` gets an H1 heading, the standard/auto-loop templates, and exit-reason values — same content, relocated.

### 2. Move rapid re-poll guard → `references/bot-polling.md` (~12 lines)

The "Rapid re-poll guard" block in Step 6c (12 lines of in-memory state-tracking rules) belongs logically in `bot-polling.md` alongside the other polling behavior. Move it there as a new H2 section. Replace the block in SKILL.md with one sentence:

```markdown
**Rapid re-poll guard**: Before looping back via Step 6c.3, apply the rapid re-poll guard described in `references/bot-polling.md` — if the same bot set triggers two consecutive immediate loop-backs with no intervening non-skip plan, fall through to the 60-second polling loop instead.
```

### 3. Prune Notes section — remove 5 notes that duplicate step content (~20 lines)

| Note | Why remove |
|------|-----------|
| **Bot display-name shortening** | Only says "see Step 13" — no new info |
| **Security — untrusted input** | 5-sentence paragraph restating Steps 5, 6, and 7 |
| **Auto-loop mode** | Long paragraph restating Arguments section + Steps 7/13 |
| **All-skip repoll** | Restates Step 6c |
| **Review threads vs. PR comments** | Restates Steps 2b/11/12 |

Keep notes that add new information not already in the steps: Keyring access, Temp files, Multiple reviewers credit, Draft PRs, Suggestion conflicts, Large PRs, Post-implementation validation.

### 4. Remove Step 7 "Action values" legend (~8 lines)

The six action values are already defined in Step 6 where each action is introduced, and are visible in the example plan table above the legend. Remove the legend block and the `> Tip` line. Keep only the Responses block (`y`/`n`/`auto`) which is unique to Step 7.

### 5. Tighten Step 6b constraints → one sentence (~3 lines)

Replace the four-bullet Constraints block with:

```markdown
**Constraints:** Lightweight identifier matching in the diff only (no AST/semantic analysis), one pass (no cascading), false positives/negatives acceptable — CI and human review catch what this misses.
```

### 6. Tighten `--auto` argument examples (~3 lines)

Replace the four example bullets + follow-up note (lines 30–35) with a single compact line:

```markdown
Examples: `/pr-comments --auto`, `/pr-comments --auto 5`, `/pr-comments #42 --auto`, `/pr-comments --auto 5 42`. A number immediately after `--auto` is always the iteration cap, not a PR number.
```

## Invariants (unchanged)

- All workflow steps preserved, in the same order, with the same numbers
- No changes to existing reference files `graphql-queries.md` or `security.md`
- All behavior (decision logic, command sequences, retry rules, error handling) unchanged
- No evals needed — pure documentation refactor

## Estimated savings

| Change | Lines saved |
|--------|-------------|
| Extract Step 14 templates | ~60 |
| Prune 5 Notes entries | ~20 |
| Move rapid re-poll guard | ~12 |
| Remove Step 7 action values legend | ~8 |
| Tighten Step 6b constraints | ~3 |
| Tighten `--auto` examples | ~3 |
| **Total** | **~106** |

Target: ~463 lines (from 569).

## Files to create/modify

- `skills/pr-comments/SKILL.md` — apply all 6 changes above
- `skills/pr-comments/references/report-templates.md` — new file, content from Step 14
- `skills/pr-comments/references/bot-polling.md` — append rapid re-poll guard section

## Tasks

See `tasks.md`.
