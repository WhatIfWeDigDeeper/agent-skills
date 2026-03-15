# pr-comments Benchmark Results

**Model**: claude-sonnet-4-6
**Date**: 2026-03-11
**Evals**: 3 (1 run each, with-skill vs. without-skill)

## Summary

| Metric | with-skill | without-skill | Delta |
|--------|-----------|--------------|-------|
| Pass rate | **100.0%** ± 0.0% | 18.5% ± 8.8% | **+82%** |
| Time | 49.0s ± 3.6s | 17.0s ± 1.0s | +32.0s |
| Tokens | 5,200 ± 400 | 2,100 ± 100 | +3,100 |

The skill adds ~32s and ~3100 tokens overhead and improves correctness by +82 percentage points. The baseline's 18.5% is inflated by accidental passes (e.g., "declined thread not resolved" passes because the baseline never resolves any threads).

## Per-Eval Results

| # | Eval | with-skill | without-skill | Key differentiators |
|---|------|-----------|--------------|---------------------|
| 1 | Basic address comments | **8/8 (100%)** | 1/8 (12.5%) | GraphQL thread state, upfront plan, Co-authored-by, resolveReviewThread |
| 2 | Explicit PR with suggestions | **7/7 (100%)** | 1/7 (14.3%) | Suggestion block detection, branch checkout, outdated thread filtering |
| 3 | Decline out-of-scope | **7/7 (100%)** | 2/7 (28.6%) | Decline plan section, reply to declined comment, correct resolve/skip split |

## What Each Eval Tests

### Eval 1 — Basic address comments
**Prompt**: `address the review comments on my PR`

Tests the core workflow: fetching inline comments via REST, checking thread state via GraphQL, presenting a categorized plan before making changes, waiting for user confirmation, committing with Co-authored-by credit, and resolving threads via `resolveReviewThread` mutation. The without-skill run fetched the wrong comment endpoint and skipped all downstream steps.

### Eval 2 — Explicit PR with suggestions
**Prompt**: `/pr-comments 47`

Tests the explicit PR number path and suggestion handling: passing the number to `gh pr view`, detecting ` ```suggestion ``` ` fenced blocks as GitHub suggested changes, applying them as local file edits (not via API), checking out the PR's head branch if needed, and filtering already-resolved and outdated threads before presenting the plan. Without the skill, suggestion blocks were not recognized as a special feature and no branch checkout was performed.

### Eval 3 — Decline out-of-scope
**Prompt**: PR with one out-of-scope auth rewrite comment mixed in with valid session management comments.

Tests the decline workflow: categorizing the out-of-scope comment as "Will decline" in the upfront plan, posting a reply explaining the scope decision, and leaving that thread unresolved while resolving the addressed threads. The without-skill run lacked the structured plan, didn't know the reply endpoint, and committed without Co-authored-by trailers.

## Known Eval Limitations

- All evals are narrated/simulated — no real GitHub PR exists. Assertions verify planned behavior against the skill's documented workflow.
- The "gh pr view used to identify PR" assertion passes in both configurations and is not discriminating; it may be dropped from future iterations.
- The "declined thread not resolved" assertion in eval 3 passes by accident in the baseline (the baseline never resolves any threads). It should be paired with a check that addressed threads ARE resolved.
- Zero variance in with-skill pass rates across all 3 evals — skill instructions are complete and consistently followed.
