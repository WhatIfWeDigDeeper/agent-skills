# Tasks: Spec 10 — pr-comments SKILL.md slim-down

## Implementation

- [ ] Create `skills/pr-comments/references/report-templates.md` with content extracted from Step 14 (standard report template, auto-loop summary table, exit reason values)
- [ ] Append rapid re-poll guard as a new H2 section to `skills/pr-comments/references/bot-polling.md`
- [ ] Replace Step 14 body in SKILL.md with a one-sentence pointer to `references/report-templates.md`
- [ ] Replace the rapid re-poll guard block in Step 6c with a one-sentence pointer to `references/bot-polling.md`
- [ ] Remove 5 Notes entries that duplicate step content: "Bot display-name shortening", "Security — untrusted input", "Auto-loop mode", "All-skip repoll", "Review threads vs. PR comments"
- [ ] Remove Step 7 "Action values" legend block and the `> Tip` line
- [ ] Tighten Step 6b constraints block to one sentence
- [ ] Tighten `--auto` argument examples to a single compact line

## Verification

- [ ] `wc -l skills/pr-comments/SKILL.md` — confirm under 500 lines
- [ ] Grep all `references/` links in SKILL.md — verify each target file exists
- [ ] Read through SKILL.md end-to-end — confirm no dangling step references or broken cross-links
- [ ] Confirm all 5 removed Notes were fully covered in their respective steps before removal
- [ ] `uv run --with pytest pytest tests/` — no test breakage
- [ ] `npx cspell skills/pr-comments/SKILL.md skills/pr-comments/references/*.md` — no spelling errors
