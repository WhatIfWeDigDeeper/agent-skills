# Tasks: Spec 37 — pr-human-guide security hardening v2

- [x] Create spec directory and plan.md
- [ ] Create feature branch `spec-37-pr-human-guide-security-v2`
- [ ] Create `skills/pr-human-guide/references/marker-helper.py` (static replacement for inline codegen)
- [ ] Edit SKILL.md — Step 1: add `^[1-9][0-9]*$` validation for `pr_number`
- [ ] Edit SKILL.md — add `## Security model` section between `## Arguments` and `## Process`
- [ ] Edit SKILL.md — Step 3: add `<untrusted_pr_content>` boundary tags around PR title/body/diff
- [ ] Edit SKILL.md — Step 4: replace inline Python codegen notes with `marker-helper.py` invocation
- [ ] Edit SKILL.md — Step 5: strengthen marker-injection guard note
- [ ] Edit SKILL.md — bump version `0.8` → `0.9`
- [ ] Create `tests/pr-human-guide/test_argument_validation.py`
- [ ] Run `uv run --with pytest pytest tests/` — verify all pass
- [ ] Update `evals/security/pr-human-guide.baseline.json` notes
- [ ] Run `npx cspell` on changed files — add any new words to cspell.config.yaml
- [ ] Commit all changes (including staged SIGPIPE rule in CLAUDE.md + copilot-instructions.md)
- [ ] Open PR; run `/pr-comments`; run `/pr-human-guide`
