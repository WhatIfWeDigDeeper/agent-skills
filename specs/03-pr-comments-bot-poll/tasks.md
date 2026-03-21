# Tasks: pr-comments Bot Review Polling

## Implementation

- [ ] **Update `skills/pr-comments/SKILL.md` Step 13**
  - After the "If the user confirms" block (push + re-request bots via REST), add:
    - Offer to poll only when bot reviewers were re-requested
    - Polling logic: 60s interval, GraphQL thread query, compare thread IDs against pre-push snapshot
    - Timeout at 10 minutes with fallback message
    - On detection: loop back to Step 2, run through to Step 7 (plan/confirm gate), then Steps 8–14
    - Loop behavior: re-offer polling after each round that re-requests a bot reviewer; user decides each time
  - Update Step 14 report template to include the poll path variant

## Evals

- [ ] **Add eval 12 to `evals/pr-comments/evals.json`**: Bot poll — user confirms polling, bot responds with 1 new thread, skill processes it
- [ ] **Add eval 13 to `evals/pr-comments/evals.json`**: Bot poll — user declines polling, skill reports normally
- [ ] **Add eval 14 to `evals/pr-comments/evals.json`**: Bot poll — timeout path (bot doesn't respond within 10 min)

## Tests

- [ ] **Add tests to `tests/pr-comments/`** covering:
  - Poll offered only when bot reviewers present (not for human-only re-requests)
  - Poll not offered when reviewer list is empty
  - Timeout fallback message

## Benchmark

- [ ] Run evals for the updated skill after implementation
- [ ] Update `evals/pr-comments/benchmark.json` with new results (evals 12–14)
- [ ] Update `evals/pr-comments/benchmark.md` summary
- [ ] Update `README.md` Eval Δ column
