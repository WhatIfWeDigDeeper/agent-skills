# Tasks: Spec 11 — pr-comments review improvements

## Implementation

### Security
- [ ] Add 4 new screening categories to `skills/pr-comments/references/security.md`: unicode/homoglyph attacks, hidden text (HTML comments, zero-width chars, collapsed details), multi-comment coordination, URL/link injection

### Structural simplification
- [ ] Add "## Entry Point: All-Skip Repoll Gate" section to `skills/pr-comments/references/bot-polling.md` with the Step 6c conditional logic (5 sub-steps: actionable check, pending bot check, post-fetch review check, immediate loop-back vs poll branch, no-bots fallthrough)
- [ ] Add "## Bot Display Names" section to `skills/pr-comments/references/bot-polling.md` with the 4-step display-name shortening algorithm currently in Step 13
- [ ] Slim Step 6c in SKILL.md: keep the actionable-vs-skip threshold check, replace the 5-sub-step body with a pointer to `references/bot-polling.md` — Entry Point: All-Skip Repoll Gate
- [ ] Slim Step 13 in SKILL.md: replace the 4-step display-name algorithm with a one-line reference to `references/bot-polling.md` — Bot Display Names
- [ ] Bump version to `1.13` in SKILL.md frontmatter

### Eval hardening
- [ ] Eval 13: add assertion that push completes before poll offer is presented
- [ ] Eval 16: add assertion that reply-author matching uses exact `login` string comparison (not role/pronoun)
- [ ] Eval 21: rewrite scenario so the identifier appears in similar-looking context in both files (e.g., both inside async functions) but with semantically different usage — making false-positive avoidance non-trivial
- [ ] Update CLAUDE.md line ~114: remove evals 13 and 16 as examples of "acceptable non-discriminating evals" — after hardening they will be discriminating

## Verification

- [ ] `wc -l skills/pr-comments/SKILL.md` — confirm reduced (target ~440 lines)
- [ ] Grep all `references/` links in SKILL.md — verify each target file and section header exists
- [ ] Read through SKILL.md end-to-end — confirm no dangling references or broken cross-links
- [ ] Read through bot-polling.md end-to-end — confirm the three entry points (Step 13, Step 3, Step 6c) are consistently documented
- [ ] `uv run --with pytest pytest tests/` — no test breakage
- [ ] `npx cspell skills/pr-comments/SKILL.md skills/pr-comments/references/*.md` — no spelling errors
- [ ] Re-run evals 13, 16, 21 (with_skill + without_skill) — confirm discrimination improves
- [ ] Update `evals/pr-comments/benchmark.json` with new eval results
- [ ] Update `README.md` Eval Δ column if pass-rate delta changes
