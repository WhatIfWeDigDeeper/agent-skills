# Spec 24: Tasks — learn "Minimum viable rule text"

## Phase 1: Edit

- [x] **1.1** In `skills/learn/SKILL.md`, replace the final `## Guidelines` bullet (the one beginning "Strip obvious explanations from rule text") with the new "Minimum viable rule text" bullet (see plan.md for exact text)
- [x] **1.2** Bump `metadata.version` from `"0.7"` to `"0.8"` in `skills/learn/SKILL.md` frontmatter

---

## Phase 2: Verification

- [x] **2.1** `rg "Strip obvious explanations" skills/learn/SKILL.md` → assert no matches
- [x] **2.2** `rg "Minimum viable rule text" skills/learn/SKILL.md` → assert exactly one match
- [x] **2.3** Confirm `## Guidelines` still has exactly 3 bullets
- [x] **2.4** Confirm `metadata.version: "0.8"` in frontmatter
- [x] **2.5** `npx cspell skills/learn/SKILL.md` — fix any unknown words in `cspell.config.yaml` (npm cache permission error unrelated to changes; no new words added)
- [x] **2.6** `uv run --with pytest pytest tests/` — 804 passed, no regressions

---

## Phase 3: Ship

- [ ] **3.1** Commit on branch `docs/minimum-viable-rule-text`: `feat(learn): rename guideline to "Minimum viable rule text" and emphasize brevity`
- [ ] **3.2** Push and open PR; run `/pr-comments` after PR is created per project convention
- [ ] **3.3** Squash-merge, delete branch, sync local main

---

## Phase 4: Downstream (application-tracker — after upstream merge)

- [ ] **4.1** Branch `chore/sync-learn-skill` from main
- [ ] **4.2** `npx skills add -y whatifwedigdeeper/agent-skills`
- [ ] **4.3** Inspect diff — confirm changes limited to `.agents/skills/learn/SKILL.md` + `skills-lock.json`. If unrelated skill changes appear, decide: either broaden the PR intentionally or constrain the sync to learn-only before committing.
- [ ] **4.4** Commit, push, PR, merge
