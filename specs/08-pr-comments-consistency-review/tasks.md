# Tasks: Spec 08 — pr-comments Cross-File Consistency Review

## Implementation

- [ ] Update `skills/pr-comments/SKILL.md`:
  - Add Step 6b: cross-file consistency check (between Steps 6 and 7)
  - Step 7: add `consistency` to action values table; note auto-mode interaction (forces manual confirmation)
  - Step 10: note consistency changes grouped with originating comment's commit
  - Notes section: add CI/validation note
  - Version bump: 1.8 → 1.10

## Tests

- [ ] Add tests for `consistency` action classification in `tests/pr-comments/`

## New Evals

- [ ] Add eval 20 (cross-file consistency: matching rename) to `evals/pr-comments/evals.json`
- [ ] Add eval 21 (cross-file consistency: no false positive) to `evals/pr-comments/evals.json`

## Verification

- [ ] Run `uv run --with pytest pytest tests/pr-comments/` — all existing tests pass
- [ ] Run eval suite (evals 1–22), update `evals/pr-comments/benchmark.json`
- [ ] Update `evals/pr-comments/benchmark.md` with new results
- [ ] Update `Eval Δ` column in `README.md`
