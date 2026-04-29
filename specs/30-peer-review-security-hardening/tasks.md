# Spec 30: Tasks — peer-review security hardening

## Phase 0: Pre-spec peer review (consistency pass on plan.md and tasks.md)

*Catch drift between `plan.md` and `tasks.md` before any SKILL.md edits are committed. Uses an external CLI reviewer for fresh-context judgment on the spec docs themselves. Auto-approves valid findings; iteration cap 2.*

- [ ] **0.1** Create branch `spec-30-peer-review-security-hardening`. (No worktree needed — this spec is small and does not run sub-agent fleets; a plain feature branch is sufficient.) Stage `specs/30-peer-review-security-hardening/plan.md` and `tasks.md`.
- [ ] **0.2** Run `/peer-review specs/30-peer-review-security-hardening/ --model copilot:gpt-5.4` (consistency mode — peer-review auto-detects this from the directory target). Auto-approve every finding the reviewer classifies as valid; record skipped/declined findings inline with reason. Iteration cap 2 — re-run after applying iteration 1's findings, then stop regardless of whether iteration 2 introduced new findings. The cap is deliberately lower than Phase 4's cap of 4 because the surface area here is two short spec docs.
- [ ] **0.3** Record per-iteration summary inline in this task. Format per spec-26/27/28 precedent: `Iteration N: K valid findings (X critical, Y major, Z minor). Applied all. {Brief note on themes.}`
- [ ] **0.4** Commit the post-review spec docs as a single commit on the branch before Phase 1 begins. This commit is the start of the spec-30 PR; SKILL.md edits from Phase 1 land as subsequent commits on the same branch.

---

## Phase 1: Edits to `skills/peer-review/SKILL.md`

- [ ] **1.1** Edit A — insert "Validate parsed arguments before use" block immediately before the line `### 2. Collect Content`. Three bullets (`--pr`, `--branch`, `--model`) per plan.md "Edit A".
- [ ] **1.2** Edit B (branch) — change the bash line `git diff ${DEFAULT_BRANCH}...NAME` to `git diff "${DEFAULT_BRANCH}...${BRANCH}"`. Add a sentence under the fenced block clarifying that `${BRANCH}` is the validated `--branch` value.
- [ ] **1.3** Edit B (PR) — in the bash block under **PR** (`--pr N`), change `gh pr view N` → `gh pr view "$PR"` and `gh pr diff N` → `gh pr diff "$PR"`. Add a sentence clarifying `$PR` is the validated integer from `--pr N`.
- [ ] **1.4** Edit C (diff template) — replace `[DIFF CONTENT]` placeholder with the six-line `<untrusted_diff>` block per plan.md "Edit C".
- [ ] **1.5** Edit C (consistency template) — replace `[FILE CONTENTS]` with analogous `<untrusted_files>` block.
- [ ] **1.6** Edit C (PR-body insertion) — find the sentence beginning "Prepend the PR title and body as context to the diff" in Step 2 and update it so the title/body are inserted **inside** the `<untrusted_diff>` block.
- [ ] **1.7** Edit D — insert "Trust model." subsection immediately after the heading `### 4. Spawn Reviewer` and before `**If \`model\` is \`self\`:**`. Use exact text from plan.md "Edit D".
- [ ] **1.8** Edit E — bump `metadata.version` from `"1.7"` to `"1.8"` in frontmatter.

---

## Phase 2: Tooling

- [ ] **2.1** `npx cspell skills/peer-review/SKILL.md specs/30-peer-review-security-hardening/*.md` — if `untrusted_diff` / `untrusted_files` flagged, add to `cspell.config.yaml` `words:` list in alphabetical position. (CI runs cspell on both `skills/**/*.md` and `specs/**/*.md`.)
- [ ] **2.2** `uv run --with pytest pytest tests/` — confirm no regressions.

---

## Phase 3: Verification

- [ ] **3.1** `rg -n 'untrusted_diff' skills/peer-review/SKILL.md` → at least 3 matches.
- [ ] **3.2** `rg -n 'untrusted_files' skills/peer-review/SKILL.md` → at least 3 matches.
- [ ] **3.3** `rg -n '\$\{DEFAULT_BRANCH\}\.\.\.NAME' skills/peer-review/SKILL.md` → no matches.
- [ ] **3.4** `rg -n 'gh pr (view|diff) N\b' skills/peer-review/SKILL.md` → no matches. (`rg` uses unescaped `|` for alternation.)
- [ ] **3.5** `rg -n 'Trust model\.' skills/peer-review/SKILL.md` → exactly one match.
- [ ] **3.6** `rg -n '^  version:' skills/peer-review/SKILL.md` → `version: "1.8"`.
- [ ] **3.7** Re-read SKILL.md end-to-end; confirm boundary markers in both prompt templates and PR-body insertion lands inside `<untrusted_diff>`.
- [ ] **3.8** Manual smoke test: `/peer-review skills/peer-review/SKILL.md` (consistency mode on the modified file) returns structured findings — does not require staging.
- [ ] **3.9** Negative arg tests: `/peer-review --pr "1; echo pwned"` and `/peer-review --branch 'main; rm -rf /'` both error at the validation step.
- [ ] **3.10** *Optional* — run a small subset of `evals/peer-review/evals.json` against `--model self` to spot-check finding quality vs. v1.7 baseline.

---

## Phase 4: Peer review

*Fresh-context consistency pass before ship, to catch cross-file drift Phase 3's mechanical checks miss (stale phrase anchors, marker imbalance, validation regex vs example mismatch, plan.md ↔ tasks.md ↔ SKILL.md gaps). Exit condition: a pass produces zero valid findings. Iteration cap: 4.*

- [ ] **4.1** Commit all Phase 1–3 changes on branch `spec-30-peer-review-security-hardening`: `feat(peer-review): v1.8 — argument validation and untrusted-content boundary markers`. The commit must land before 4.2 so the branch review can see the SKILL.md changes (committed diff only; staged-only changes are not visible to `--branch`).
- [ ] **4.2** Run `/peer-review --branch spec-30-peer-review-security-hardening` (or `/peer-review --branch spec-30-peer-review-security-hardening --model copilot:gpt-5.4`) and apply valid findings. Loop until zero valid findings or iteration cap 4. Record per-iteration summary inline in this task.

---

## Phase 5: Ship

- [ ] **5.1** Push branch (implementation already committed in 4.1), open PR, immediately run `/pr-comments {pr_number}` per project convention.
- [ ] **5.2** Loop `/pr-comments` until no new bot feedback.
- [ ] **5.3** Run `/pr-human-guide` to annotate the PR for human reviewers.
- [ ] **5.4** Verify CI is green (`gh pr checks {pr_number}`) and a human has reviewed before merging.
- [ ] **5.5** `gh pr merge --squash --delete-branch`, sync local main, run `/learn` if prompted.
