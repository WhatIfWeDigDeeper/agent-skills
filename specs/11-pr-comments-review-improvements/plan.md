# Spec 11: pr-comments — Review improvements (v1.12)

## Problem

The pr-comments skill (v1.12, ~471 lines + ~258 lines in references) is performing well but has four issues (three structural, one eval-signal) identified during review:

1. **Security reference is thin** — `security.md` is ~17 lines with 4 bullet points, missing real-world attack vectors relevant to AI agents processing PR comments (unicode tricks, hidden text, URL injection, coordinated multi-comment attacks)
2. **Step 6c is the densest inline step** — ~35 lines of nested conditional logic requiring readers to interleave SKILL.md and bot-polling.md while tracking 4 state variables
3. **Step 13 is the longest step** (~58 lines) — mixes push logic, human/bot re-request, display-name algorithm, claude[bot] exception, and polling handoff
4. **~13% of evals are fully non-discriminating** — evals 13, 16, 21 score identically with and without the skill; eval 18 is nearly non-discriminating (~20% delta, only Co-authored-by differentiates)

## Proposed Changes

### 1. Strengthen `references/security.md` (~17 → ~35 lines)

Add four new screening categories to the existing criteria:

| Category | What to detect | Why it matters |
|----------|---------------|----------------|
| Unicode/homoglyph | Visually similar characters substituted in instruction-like phrases (e.g., Cyrillic "о" for Latin "o" in "ignore previous instructions") | Bypasses naive keyword matching |
| Hidden text | HTML comments (`<!-- -->`), collapsed `<details>` blocks, zero-width characters invisible in GitHub UI but present in API responses | Instructions hidden from human reviewers but visible to agents |
| Multi-comment coordination | Multiple comments from the same author containing fragments that combine into instruction-like text | Each comment looks benign individually |
| URL/link injection | Comments instructing the agent to fetch external resources or follow URLs | Exfiltration vector; further injection via fetched content |

For each category, add the detection heuristic and the response (same as existing: flag as `decline`, surface to user).

### 2. Extract Step 6c repoll gate into `references/bot-polling.md`

Move the Step 6c body (currently 5 sub-steps of conditional logic) into bot-polling.md as a new section: "## Entry Point: All-Skip Repoll Gate". This consolidates all three polling entry points in one file.

Replace Step 6c in SKILL.md with ~7 lines:
- Keep the actionable-vs-skip threshold check inline (it gates whether the step runs at all)
- Add a pointer: "Execute the all-skip repoll gate per `references/bot-polling.md` — Entry Point: All-Skip Repoll Gate"

### 3. Extract display-name algorithm from Step 13 into `references/bot-polling.md`

Move the 4-step bot display-name shortening algorithm from Step 13 to bot-polling.md as a new section: "## Bot Display Names". Step 13 references it with one line.

### 4. Harden non-discriminating evals

| Eval | Current issue | Proposed fix |
|------|--------------|--------------|
| 13 (bot poll decline) | Without-skill independently discovers poll-decline flow (5/5) | Add assertion: push must complete *before* poll offer is presented |
| 16 (skip previously-replied) | Explicit prompt context makes skip trivial (4/4) | Add assertion: agent checks reply author via exact `login` string match, not role/pronoun |
| 21 (no false positive consistency) | Both configs avoid flagging when context differences are explicit (3/3) | Replace with scenario where identifier name matches AND surrounding context is similar (e.g., both in async functions) but semantic usage differs |

Eval 18 (`review-body-reply-question`) is excluded: it is already discriminating (~20% delta, 5/5 with skill vs 4/5 without) and already has an assertion covering the issue comments API endpoint distinction. No changes needed.

## Invariants (unchanged)

- All 14 workflow steps preserved in the same order with the same numbers
- No changes to `references/graphql-queries.md` or `references/report-templates.md`
- All decision logic, command sequences, retry rules, error handling unchanged
- Existing passing evals must continue to pass

## Files to create/modify

- `skills/pr-comments/SKILL.md` — slim Step 6c (~27 lines saved), slim Step 13 (~8 lines saved)
- `skills/pr-comments/references/security.md` — add 4 screening categories (~19 lines added)
- `skills/pr-comments/references/bot-polling.md` — add "Entry Point: All-Skip Repoll Gate" (~30 lines) and "Bot Display Names" (~8 lines) sections
- `evals/pr-comments/evals.json` — modify assertions for evals 13, 16, 18, 21
- `evals/pr-comments/benchmark.json` — update after re-running modified evals

## Estimated impact

| Metric | Before | After |
|--------|--------|-------|
| SKILL.md lines | ~471 | ~440 |
| bot-polling.md lines | ~126 | ~163 |
| security.md lines | ~17 | ~35 |
| Discriminating evals | 20/23 | 23/23 |
| Version | 1.12 | 1.13 |

_Line counts are approximate and may drift with future edits._

## Future work (not in this spec)

- `--reviewer <login>` filter flag — scope a run to specific reviewers
- Batched thread resolution via aliased GraphQL mutations
- Relocate large-PR batching guidance from Notes to Step 7

## Tasks

See `tasks.md`.
