# Spec 34: Tasks — peer-review security hardening v2

## Phase 0: Pre-implementation peer review (consistency on spec docs)

*Catch drift between `plan.md` and `tasks.md` before any SKILL.md edits land. Uses `copilot:gpt-5.4` for fresh-context judgment on the spec docs themselves. Auto-approves valid findings; iteration cap 1 (the spec is two short docs — one pass is enough).*

- [x] **0.1** From the worktree (`.claude/worktrees/spec-34/`), run `/peer-review specs/34-peer-review-security-hardening-v2/ --model copilot:gpt-5.4`. Consistency mode is auto-detected from the directory target.
- [x] **0.2** When the apply prompt fires, reply `all` to auto-approve every finding the reviewer + triage classifies as recommended. (Triage already filters speculative/already-handled findings on the external-CLI path; the remaining `recommended` bucket is the auto-y set.)
- [x] **0.3** Record the iteration summary inline here. Format per spec-26/27/28/30 precedent: `Iteration 1: K valid findings (X critical, Y major, Z minor). Applied all. {Brief note on themes.}` Stop after iteration 1 regardless of whether new findings would surface in a hypothetical iteration 2 — the cap is deliberate.

  Iteration 1: 3 valid findings (0 critical, 2 major, 1 minor). Applied all. Themes: gating-vs-fallback ambiguity in the stdin verification path (findings 1 and 2 — clarified that the smoke test must be **attempted** before commit, with two acceptable outcomes; tasks.md 3.1/3.2 now have conditional expected counts depending on whether fallback was taken); plan ↔ Edit-D internal consistency (finding 3 — Out-of-Scope claimed the publisher-verification note was restated under Security model, but Edit D's bullet list omitted it; added a "Third-party CLI provenance" mitigation bullet to Edit D and tightened the Out-of-Scope wording). Re-read both spec files post-apply and caught three additional self-noticed gaps (Edit C → Edit D reference, stale "must confirm" framing in Edit A's verification block, "gates the commit" wording in the Risks section); fixed inline before commit. Stopping per cap.
- [ ] **0.4** Commit the post-review spec docs as the first commit on branch `spec-34-peer-review-security-hardening-v2`: `spec(peer-review): v1.10 hardening plan — stdin transport, secret pre-scan, security model section`. Phase 1 SKILL.md edits land as subsequent commits.

---

## Phase 1: Edits to `skills/peer-review/SKILL.md`

- [ ] **1.1** Edit B — under the `**4b. Write prompt to temp file:**` heading, add `chmod 600 "$PROMPT_FILE"` immediately after the `mktemp` line and before the `trap` line.
- [ ] **1.2** Edit A (copilot) — under the `**4c. Execute and capture output:**` heading, replace the copilot if/else block to use `< "$PROMPT_FILE"` (stdin) instead of `-p "$(cat "$PROMPT_FILE")"`. Match the exact bash from plan.md "Edit A".
- [ ] **1.3** Edit A (gemini) — same heading, replace the gemini if/else block to use `< "$PROMPT_FILE"` instead of `-p "$(cat "$PROMPT_FILE")"`. Match the exact bash from plan.md "Edit A".
- [ ] **1.4** Edit A (prose) — find the sentence beginning "In the commands below, prompt content is passed safely either as a single quoted argument" between Step 4b and 4c and replace it with the new wording from plan.md "Edit A".
- [ ] **1.5** Edit C — insert a new sub-step `**4b-bis. Pre-flight secret scan (external CLI path only):**` between Step 4b (write prompt to temp file) and Step 4c (execute and capture output). Use the exact text from plan.md "Edit C", including the seven secret patterns, the redaction-and-confirm prompt, the `**stop generating**` clause, and the `y` / anything-else branches.
- [ ] **1.6** Edit D (new section) — insert `## Security model` section immediately after the `## Review Modes` table and before `## Process`. Use the exact bullet list and "Residual risks" sub-list from plan.md "Edit D".
- [ ] **1.7** Edit D (replace existing trust-model paragraph) — find the paragraph beginning "**Trust model.** With `--model self`" at the top of Step 4 and replace the entire paragraph with the one-liner: `**See the Security model section above for the full trust model and pre-flight checks.**`
- [ ] **1.8** Edit E — bump `metadata.version` from `"1.9"` to `"1.10"` in frontmatter.

---

## Phase 2: Tooling

- [ ] **2.1** `npx cspell skills/peer-review/SKILL.md specs/34-peer-review-security-hardening-v2/*.md` — if any new tokens are flagged (`bis`, `cmdline`, `xoxb`, `xoxp`, `AKIA`, `gho`, `ghs`, `ghu`, vendor names), add to `cspell.config.yaml` `words:` list in alphabetical position.
- [ ] **2.2** `uv run --with pytest pytest tests/` — confirm no regressions.

---

## Phase 3: Verification

- [ ] **3.1** `rg -n '< "\$PROMPT_FILE"' skills/peer-review/SKILL.md` → at least 4 matches (no-fallback path: copilot if/else + gemini if/else). If 3.8 fallback was taken for one CLI, expected count drops to 2 (one CLI's if/else); if both CLIs fell back, expected count is 0 — note which path applied.
- [ ] **3.2** `rg -n '"\$\(cat "\$PROMPT_FILE"\)"' skills/peer-review/SKILL.md` → no matches (no-fallback path). If 3.8 fallback was taken, expected count is 2 per fallback CLI (the if/else branches still using argv) — note which CLIs fell back.
- [ ] **3.3** `rg -n 'chmod 600' skills/peer-review/SKILL.md` → exactly 1 match.
- [ ] **3.4** `rg -n '4b-bis' skills/peer-review/SKILL.md` → at least 2 matches (the heading and the Security-model bullet cross-reference).
- [ ] **3.5** `rg -n '^## Security model' skills/peer-review/SKILL.md` → exactly 1 match.
- [ ] **3.6** `rg -n 'Trust model\.' skills/peer-review/SKILL.md` → no matches (replaced by the cross-reference one-liner).
- [ ] **3.7** `rg -n '^  version:' skills/peer-review/SKILL.md` → `version: "1.10"`.
- [ ] **3.8** **Manual stdin verification (must be attempted before commit; fallback is allowed)**: `echo "say hi" | copilot --allow-all-tools --deny-tool='write' 2>&1 | head -20` and `echo "say hi" | gemini --approval-mode plan 2>&1 | head -20`. Two acceptable outcomes — do not commit without one of them: (a) both CLIs produce a normal response, in which case Edits A/B land as written and 3.1/3.2 use the no-fallback expected counts; or (b) one or both CLIs reject piped stdin (drops into interactive mode, errors on empty `-p`, or hangs), in which case revert that CLI's block to argv + `chmod 600` and update Edit A's prose plus Edit D's "Residual risks" to name the affected CLI. Re-run 3.1–3.2 using the conditional expected counts inline in those steps.
- [ ] **3.9** Manual secret-scan smoke test: stage a fixture file containing a fake `ghp_aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa`, run `/peer-review --staged --model copilot`, confirm the secret prompt fires before any CLI call and that replying `n` exits cleanly with `Aborted — redact secrets and re-run.`
- [ ] **3.10** Spec 30 regression: `/peer-review --pr "1; echo pwned"` and `/peer-review --branch 'main; rm -rf /'` both still error at Step 1 validation.
- [ ] **3.11** Re-read SKILL.md end-to-end; confirm Edits A–E land in the right places, phrase anchors still match, and no orphaned `[FOCUS_LINE]` / `[FOCUS_AREA_LINE]` placeholders were introduced.

---

## Phase 4: Post-implementation peer review (consistency, copilot:gpt-5.4, iter cap 3)

*Fresh-context consistency pass after SKILL.md edits land, to catch cross-file drift the Phase 3 mechanical checks miss (spec ↔ SKILL.md gaps, marker imbalance, validation regex vs example mismatch, stale phrase anchors). Same model as Phase 0 (`copilot:gpt-5.4`) for comparable judgment.*

- [ ] **4.1** Commit Phase 1–3 changes on branch `spec-34-peer-review-security-hardening-v2`: `feat(peer-review): v1.10 — stdin transport, pre-flight secret scan, consolidated security model`.
- [ ] **4.2** Run `/peer-review specs/34-peer-review-security-hardening-v2/ --model copilot:gpt-5.4` (consistency mode — auto-detected from the directory target). The spec dir now reflects the implemented SKILL.md state; this catches plan ↔ tasks drift introduced during implementation. Apply valid findings (reply `all` to auto-approve). Loop until zero valid recommended findings or iteration cap 3. Record per-iteration summary inline.
- [ ] **4.3** Run a single consistency pass on `skills/peer-review/SKILL.md` itself: `/peer-review skills/peer-review/SKILL.md --model copilot:gpt-5.4`. Same auto-`all` apply policy. One pass only — Phase 5 PR review will catch anything subtler. Record the iteration summary inline.

---

## Phase 5: Ship

- [ ] **5.1** Push branch (already committed in 4.1), open PR, immediately run `/pr-comments {pr_number}`.
- [ ] **5.2** Loop `/pr-comments` until no new bot feedback.
- [ ] **5.3** Run `/pr-human-guide` to annotate the PR for human reviewers.
- [ ] **5.4** Verify CI is green (`gh pr checks {pr_number}`) and a human has reviewed before merging.
- [ ] **5.5** `gh pr merge --squash --delete-branch`, sync local main, run `/learn` if prompted.
- [ ] **5.6** **Post-merge follow-up** — once `skills.sh` re-scans the merged version, re-fetch the three scanner pages (agent-trust-hub, snyk, socket) and confirm the FAILs flip to PASS or move to documented residual-risk findings. If any real finding remains, open a follow-up spec.
