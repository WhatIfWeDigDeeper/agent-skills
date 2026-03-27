# Tasks: Spec 12 -- pr-comments timeline comment support

## Implementation

### SKILL.md changes
- [x] Bump version to `"1.14"` in frontmatter
- [x] Add "timeline comments" to skill description
- [x] Add timeline comments row to tool choice table
- [x] Add Step 2c: Fetch PR Timeline Comments (endpoint, filters, dedup, already-addressed detection)
- [x] Update Step 3: exit check includes "no timeline comments from Step 2c"
- [x] Update Step 4: note timeline comments skip this step
- [x] Update Step 5: security screening covers timeline comments
- [x] Update Step 6: broaden classification to "review body and timeline comments (Steps 2b and 2c)"
- [x] Update Step 7: add `*(timeline)*` row to plan table example
- [x] Update Step 11: clarify timeline reply routing (same endpoint as review body)
- [x] Update Step 12: note timeline comments skip resolve (no thread ID)
- [x] Update Step 13: add timeline comment authors to re-request sources

### Reference file changes
- [x] `references/bot-polling.md`: add Signal 3 (new timeline comment from polled bot)
- [x] `references/bot-polling.md`: update all-skip repoll gate to check bot timeline comments after `fetch_timestamp`
- [x] `references/report-templates.md`: add skipped-line variant for timeline comments

### Tests
- [x] Add test cases for timeline comment filtering (exclude PR author, exclude authenticated user)
- [x] Add test cases for dedup logic (200-char prefix match against review bodies)
- [x] Add test cases for already-addressed detection (@mention or quote linkage required; unrelated later comment does not suppress)
- [x] Add test cases for Signal 3 bot polling: timeline-only bot response triggers loop-back to Step 2
- [x] Add test cases for all-skip repoll gate: post-fetch bot timeline comment triggers immediate re-fetch

### Evals
- [x] Add evals 24–27 to `evals/pr-comments/evals.json`
- [x] Run evals 24–27 with_skill and without_skill
- [x] Grade results and update `evals/pr-comments/benchmark.json`
- [x] Update `benchmark.json` metadata: append eval IDs 24–27 to `metadata.evals_run`; set `metadata.skill_version` to `"1.14"`
- [x] Update `README.md` Eval delta column if pass-rate delta changes

## Verification

- [x] `uv run --with pytest pytest tests/` -- no test breakage
- [x] `npx cspell skills/pr-comments/SKILL.md skills/pr-comments/references/bot-polling.md skills/pr-comments/references/report-templates.md`
- [x] Grep all `references/` links in SKILL.md -- verify each target exists
- [x] Read through SKILL.md end-to-end -- confirm no dangling references
- [x] Read through bot-polling.md -- confirm Signal 3 is consistently referenced
