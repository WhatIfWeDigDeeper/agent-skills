# Tasks: Spec 12 -- pr-comments timeline comment support

## Implementation

### SKILL.md changes
- [ ] Bump version to `"1.14"` in frontmatter
- [ ] Add "timeline comments" to skill description
- [ ] Add timeline comments row to tool choice table
- [ ] Add Step 2c: Fetch PR Timeline Comments (endpoint, filters, dedup, already-addressed detection)
- [ ] Update Step 3: exit check includes "no timeline comments from Step 2c"
- [ ] Update Step 4: note timeline comments skip this step
- [ ] Update Step 5: security screening covers timeline comments
- [ ] Update Step 6: broaden classification to "review body and timeline comments (Steps 2b and 2c)"
- [ ] Update Step 7: add `*(timeline)*` row to plan table example
- [ ] Update Step 11: clarify timeline reply routing (same endpoint as review body)
- [ ] Update Step 12: note timeline comments skip resolve (no thread ID)
- [ ] Update Step 13: add timeline comment authors to re-request sources

### Reference file changes
- [ ] `references/bot-polling.md`: add Signal 3 (new timeline comment from polled bot)
- [ ] `references/bot-polling.md`: update all-skip repoll gate to check bot timeline comments after `fetch_timestamp`
- [ ] `references/report-templates.md`: add skipped-line variant for timeline comments

### Tests
- [ ] Add test cases for timeline comment filtering (exclude PR author, exclude authenticated user)
- [ ] Add test cases for dedup logic (200-char prefix match against review bodies)
- [ ] Add test cases for already-addressed detection (@mention or quote linkage required; unrelated later comment does not suppress)
- [ ] Add test cases for Signal 3 bot polling: timeline-only bot response triggers loop-back to Step 2
- [ ] Add test cases for all-skip repoll gate: post-fetch bot timeline comment triggers immediate re-fetch

### Evals
- [ ] Add evals 24–27 to `evals/pr-comments/evals.json`
- [ ] Run evals 24–27 with_skill and without_skill
- [ ] Grade results and update `evals/pr-comments/benchmark.json`
- [ ] Update `benchmark.json` metadata: append eval IDs 24–27 to `metadata.evals_run`; set `metadata.skill_version` to `"1.14"`
- [ ] Update `README.md` Eval delta column if pass-rate delta changes

## Verification

- [ ] `uv run --with pytest pytest tests/` -- no test breakage
- [ ] `npx cspell skills/pr-comments/SKILL.md skills/pr-comments/references/bot-polling.md skills/pr-comments/references/report-templates.md`
- [ ] Grep all `references/` links in SKILL.md -- verify each target exists
- [ ] Read through SKILL.md end-to-end -- confirm no dangling references
- [ ] Read through bot-polling.md -- confirm Signal 3 is consistently referenced
