# Tasks: Spec 07 — pr-comments Review Body Actionable

## Implementation

- [x] Update `skills/pr-comments/SKILL.md`:
  - Step 2b: remove "informational only" paragraph; add note about issue comments reply endpoint
  - Step 6: add review body comments to decision flow; add `skip` criteria; note no `diff_hunk` context
  - Step 7: remove `review-body` from action values table
  - Step 11: add note distinguishing the two reply endpoints; use issue comments API for review body replies
  - Step 12: add note to skip resolveReviewThread for review body items
  - Step 14: remove `{review-body line}` from report template; update Notes section
  - Version bump: update the `pr-comments` skill version appropriately (for example, 1.6 → 1.7 at the time of this spec)

## New Evals

- [x] Add eval 17 (review body: skip and decline) to `evals/pr-comments/evals.json`
- [x] Add eval 18 (review body: reply to question) to `evals/pr-comments/evals.json`

## Verification

- [x] Run `uv run --with pytest pytest tests/pr-comments/` — all existing tests pass (114 passing)
- [x] Run eval suite (evals 17–18), update `evals/pr-comments/benchmark.json`
- [x] Update `evals/pr-comments/benchmark.md` with new results
- [x] Update `Eval Δ` column in `README.md` (+62% → +58%)
