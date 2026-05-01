# Spec 34: Tasks — peer-review security hardening v2

## Phase 0: Pre-implementation peer review (consistency on spec docs)

*Catch drift between `plan.md` and `tasks.md` before any SKILL.md edits land. Uses `copilot:gpt-5.4` for fresh-context judgment on the spec docs themselves. Auto-approves valid findings; iteration cap 1 (the spec is two short docs — one pass is enough).*

- [x] **0.1** From the worktree (`.claude/worktrees/spec-34/`), run `/peer-review specs/34-peer-review-security-hardening-v2/ --model copilot:gpt-5.4`. Consistency mode is auto-detected from the directory target.
- [x] **0.2** When the apply prompt fires, reply `all` to auto-approve every finding the reviewer + triage classifies as recommended. (Triage already filters speculative/already-handled findings on the external-CLI path; the remaining `recommended` bucket is the auto-y set.)
- [x] **0.3** Record the iteration summary inline here. Format per spec-26/27/28/30 precedent: `Iteration 1: K valid findings (X critical, Y major, Z minor). Applied all. {Brief note on themes.}` Stop after iteration 1 regardless of whether new findings would surface in a hypothetical iteration 2 — the cap is deliberate.

  Iteration 1: 3 valid findings (0 critical, 2 major, 1 minor). Applied all. Themes: gating-vs-fallback ambiguity in the stdin verification path (findings 1 and 2 — clarified that the smoke test must be **attempted** before commit, with two acceptable outcomes; tasks.md 3.1/3.2 now have conditional expected counts depending on whether fallback was taken); plan ↔ Edit-D internal consistency (finding 3 — Out-of-Scope claimed the publisher-verification note was restated under Security model, but Edit D's bullet list omitted it; added a "Third-party CLI provenance" mitigation bullet to Edit D and tightened the Out-of-Scope wording). Re-read both spec files post-apply and caught three additional self-noticed gaps (Edit C → Edit D reference, stale "must confirm" framing in Edit A's verification block, "gates the commit" wording in the Risks section); fixed inline before commit. Stopping per cap.
- [x] **0.4** Commit the post-review spec docs as the first commit on branch `spec-34-peer-review-security-hardening-v2`: `spec(peer-review): v1.10 hardening plan — stdin transport, secret pre-scan, security model section`. Phase 1 SKILL.md edits land as subsequent commits. (Commit `0a37a0a`.)

---

## Phase 1: Edits to `skills/peer-review/SKILL.md`

- [x] **1.1** Edit B — under the temp-file-write heading (`**4c. Write prompt to temp file:**` post-Edit-C; was `**4b.**` in v1.9), add `chmod 600 "$PROMPT_FILE"` immediately after the `mktemp` line and before the `trap` line.
- [x] **1.2** Edit A (copilot) — under the execute heading (`**4d. Execute and capture output:**` post-Edit-C; was `**4c.**` in v1.9), replace the copilot if/else block to use `< "$PROMPT_FILE"` (stdin) instead of `-p "$(cat "$PROMPT_FILE")"`. Match the exact bash from plan.md "Edit A".
- [x] **1.3** Edit A (gemini) — same heading, replace the gemini if/else block to use `< "$PROMPT_FILE"` instead of `-p "$(cat "$PROMPT_FILE")"`. Match the exact bash from plan.md "Edit A".
- [x] **1.4** Edit A (prose) — find the sentence beginning "In the commands below, prompt content is passed safely either as a single quoted argument" between the temp-file-write step (`**4c.**` post-Edit-C) and the execute step (`**4d.**`) and replace it with the new wording from plan.md "Edit A".
- [x] **1.5** Edit C — insert a new sub-step `**4b. Pre-flight secret scan (external CLI path only):**` immediately before the v1.9 `**4b. Write prompt to temp file:**` heading (which renumbers to `**4c.**`). Use the exact text from plan.md "Edit C", including the seven secret patterns, the redaction-and-confirm prompt, the `**stop generating**` clause, and the `y` / anything-else branches.
- [x] **1.6** Edit D (new section) — insert `## Security model` section immediately after the `## Review Modes` table and before `## Process`. Use the exact bullet list and "Residual risks" sub-list from plan.md "Edit D".
- [x] **1.7** Edit D (replace existing trust-model paragraph) — find the paragraph beginning "**Trust model.** With `--model self`" at the top of Step 4 and replace the entire paragraph with the one-liner: `**See the Security model section above for the full trust model and pre-flight checks.**`
- [x] **1.8** Edit E — bump `metadata.version` from `"1.9"` to `"1.10"` in frontmatter.

---

## Phase 2: Tooling

- [x] **2.1** `npx cspell skills/peer-review/SKILL.md specs/34-peer-review-security-hardening-v2/*.md` — add any newly-flagged tokens to `cspell.config.yaml` `words:` list in alphabetical position. (Added `AKIA`, `baprs`, `cmdline`, `xoxb`, `xoxp` in commit `0a37a0a`; `lookarounds` and `PCRE` added later in the implementation. `bis` was not needed — Edit C's heading was renamed to `4b. Pre-flight secret scan` during round-4 review. `gho`/`ghs`/`ghu` appear only inside fenced regex code blocks, which cspell ignores by default.)
- [x] **2.2** `uv run --with pytest pytest tests/` — confirm no regressions. (830 tests passed.)

---

## Phase 3: Verification

- [x] **3.1** `rg -n '< "\$PROMPT_FILE"' skills/peer-review/SKILL.md` → at least 4 matches (no-fallback path: copilot if/else + gemini if/else). If 3.8 fallback was taken for one CLI, expected count drops to 2 (one CLI's if/else); if both CLIs fell back, expected count is 0 — note which path applied. (4 matches — no fallback.)
- [x] **3.2** `rg -n '"\$\(cat "\$PROMPT_FILE"\)"' skills/peer-review/SKILL.md` → no matches (no-fallback path). If 3.8 fallback was taken, expected count is 2 per fallback CLI (the if/else branches still using argv) — note which CLIs fell back. (0 matches — no fallback.)
- [x] **3.3** `rg -n 'chmod 600' skills/peer-review/SKILL.md` → exactly 1 match. (1 match.)
- [x] **3.4** `rg -n '4b\. Pre-flight secret scan' skills/peer-review/SKILL.md` → exactly 1 match (the heading). (1 match.)
- [x] **3.5** `rg -n '^## Security model' skills/peer-review/SKILL.md` → exactly 1 match. (1 match.)
- [x] **3.6** `rg -n 'Trust model\.' skills/peer-review/SKILL.md` → no matches (replaced by the cross-reference one-liner). (0 matches.)
- [x] **3.7** `rg -n '^  version:' skills/peer-review/SKILL.md` → `version: "1.10"`. (`version: "1.10"`.)
- [x] **3.8** **Manual stdin verification (must be attempted before commit; fallback is allowed)**: `echo "say hi" | copilot --allow-all-tools --deny-tool='write' 2>&1 | head -20` and `echo "say hi" | gemini --approval-mode plan 2>&1 | head -20`. Two acceptable outcomes — do not commit without one of them: (a) both CLIs produce a normal response, in which case Edits A/B land as written and 3.1/3.2 use the no-fallback expected counts; or (b) one or both CLIs reject piped stdin (drops into interactive mode, errors on empty `-p`, or hangs), in which case revert that CLI's block to argv + `chmod 600` and update Edit A's prose plus Edit D's "Residual risks" to name the affected CLI. Re-run 3.1–3.2 using the conditional expected counts inline in those steps. (Outcome (a) — both copilot and gemini accepted piped stdin and produced normal responses; no fallback needed.)
- [ ] **3.9** Manual secret-scan smoke test: **deferred to Phase 5.5** — stage a fixture file containing a fake `ghp_aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa`, run `/peer-review --staged --model copilot`, confirm the secret prompt fires before any CLI call and that replying `n` exits cleanly with `Aborted — redact secrets and re-run.` Interactive flow not feasible in current autonomous loop. Partial coverage already exists from Phase 4.2's own peer-review run, where the scanner correctly fired on the literal `ghp_a…` example in the spec docs themselves; Phase 5.5 completes the full smoke-test (including the `n`-aborts path).
- [x] **3.10** Spec 30 regression: verify the validation regexes (`^[1-9][0-9]*$` for `--pr`, `^[A-Za-z0-9._/-]+$` for `--branch`) still reject the canonical injection strings `1; echo pwned` and `main; rm -rf /`. Direct regex execution via `bash [[ =~ ]]` is acceptable in lieu of triggering the full slash-command flow, since the validation is well-isolated logic and the slash flow itself can't be invoked from the autonomous loop. (Both regexes rejected both injection strings via `bash [[ =~ ]]` as expected. The full `/peer-review --pr ...` / `/peer-review --branch ...` end-to-end flow remains exercised by manual invocation; an additional opportunity is the Phase 5 PR-review pass where reviewers can spot-check the slash flow.)
- [x] **3.11** Re-read SKILL.md end-to-end; confirm Edits A–E land in the right places, phrase anchors still match, and no orphaned `[FOCUS_LINE]` / `[FOCUS_AREA_LINE]` placeholders were introduced. (All edits A–E land correctly; placeholders only appear inside template code-blocks as documented; Step 4f cross-reference in Security model resolves to the correct heading.)

---

## Phase 4: Post-implementation peer review (consistency, copilot:gpt-5.4, iter cap 3)

*Fresh-context consistency pass after SKILL.md edits land, to catch cross-file drift the Phase 3 mechanical checks miss (spec ↔ SKILL.md gaps, marker imbalance, validation regex vs example mismatch, stale phrase anchors). Same model as Phase 0 (`copilot:gpt-5.4`) for comparable judgment.*

- [x] **4.1** Commit Phase 1–3 changes on branch `spec-34-peer-review-security-hardening-v2`: `feat(peer-review): v1.10 — stdin transport, pre-flight secret scan, consolidated security model`. (Commit `df83f0e`.)
- [x] **4.2** Run `/peer-review specs/34-peer-review-security-hardening-v2/ --model copilot:gpt-5.4` (consistency mode — auto-detected from the directory target). The spec dir now reflects the implemented SKILL.md state; this catches plan ↔ tasks drift introduced during implementation. Apply valid findings (reply `all` to auto-approve). Loop until zero valid recommended findings or iteration cap 3. Record per-iteration summary inline.

  Iteration 1: 4 valid findings (0 critical, 3 major, 1 minor). Applied all. Themes: (a) workflow gaps the implementation phase introduced — Phase 3.9 deferred without a corresponding Phase 5 step, and Phase 4.2/4.3 edits had no commit step before push (added 5.5 for the secret-scan smoke test and 4.4 for the post-review commit, updated 5.1 wording); (b) verification rigor — Phase 3.10 was completed via static regex inspection but the plan calls for command execution; re-ran the validation regexes directly via `bash [[ =~ ]]` against both injection strings and updated the completion note (also addressed the minor finding about brittle line-number references in the same edit).

  Iteration 2: 4 valid findings (0 critical, 4 major, 0 minor). Applied all. Themes: cascade fixes from iter1 itself — (a) marking 3.9 `[x]` while the note said "deferred" was internally contradictory (re-uncheck and reword as "deferred to 5.5"); (b) 3.10 step text still claimed slash-command re-run while the completion note showed regex-only — updated step text to make direct regex execution explicitly acceptable; (c) plan.md Verification 11/12 hadn't been updated to match the new tasks.md Phase 5.5 deferral and the regex-execution acceptance — aligned both; (d) plan.md Shipping section was missing the conditional "commit Phase 4 fixes" step that tasks.md 4.4 added — inserted as a new Shipping step. Note: each iter1 fix that was applied to only one file (tasks.md) opened a corresponding plan↔tasks drift in iter2, which is the expected behavior of consistency review.

  Iteration 3: 3 valid findings (0 critical, 2 major, 1 minor). Applied all. Themes: smaller cascade-from-iter2 + pre-existing drift the earlier iters didn't surface — (a) plan.md Risks line referenced `tasks.md 3.8` for fallback counts but those counts live in 3.1–3.2 (corrected); (b) plan.md "Files to Modify" omitted the spec docs even though the workflow edits and commits them in Phase 0/4 (renamed section to "Implementation-phase targets" and added a clarifying paragraph for the spec-doc edits); (c) tasks.md 5.5 was unconditional but plan.md Shipping step 5 made it conditional on whether 3.9 was completed pre-PR (added "if not already completed in 3.9" to 5.5). Hitting iter cap 3 — stop loop here even if a hypothetical iter4 would surface more cascade findings, per the spec design.
- [x] **4.3** Run a single consistency pass on `skills/peer-review/SKILL.md` itself: `/peer-review skills/peer-review/SKILL.md --model copilot:gpt-5.4`. Same auto-`all` apply policy. One pass only — Phase 5 PR review will catch anything subtler. Record the iteration summary inline.

  Pass complete: 5 valid findings (1 critical, 3 major, 1 minor). Applied all. Themes: (a) Security-model contract gap — the bullet promising `<untrusted_*>` boundary markers in "every reviewer prompt" was contradicted by the Step 4e triage prompt template, which inlined `[COLLECTED CONTENT ...]` raw with no tags or "treat as data only" warning; fixed by wrapping the placeholder in mode-conditional `<untrusted_files>` / `<untrusted_diff>` tags with the same warning Step 3 uses; (b) error-path completeness — branch detection had no failure mode if both `origin/HEAD` and `git remote show origin` returned empty (added explicit guard with actionable `git remote set-head origin --auto` hint), and Step 4d parse-failure was undefined relative to Step 4e/Step 6 (clarified as terminal output); (c) no-shell directive completeness — directory existence check via `Read` on "any file under it" never said how to discover that file non-shell (added explicit `Glob` listing step before `Read`, with the empty-list path as the existence-check failure mode); (d) usage-text drift — auto-detect summary said "prompt if both exist" but Step 2 actually offers `staged/unstaged/all` (aligned the prompt wording in usage). cspell clean post-edits.
- [x] **4.4** If Phases 4.2 or 4.3 produced any file edits, commit them on `spec-34-peer-review-security-hardening-v2` with message `chore(peer-review): apply post-implementation peer-review fixes`. If no edits were applied, skip this step (note "no Phase 4 fixes applied" inline). (Commit `b696400`.)

---

## Phase 5: Ship

- [x] **5.1** Push branch (Phase 1–3 commit + any Phase 4.4 commits), open PR, immediately run `/pr-comments {pr_number}`.
- [ ] **5.2** Loop `/pr-comments` until no new bot feedback.
- [ ] **5.3** Run `/pr-human-guide` to annotate the PR for human reviewers.
- [ ] **5.4** Verify CI is green (`gh pr checks {pr_number}`) and a human has reviewed before merging.
- [ ] **5.5** **Manual secret-scan smoke test (deferred from 3.9)** — if not already completed in 3.9, stage a fixture file containing a fake `ghp_aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa`, run `/peer-review --staged --model copilot`, confirm the secret prompt fires before any CLI call and that replying `n` exits cleanly with `Aborted — redact secrets and re-run.` Record the result inline. Run before the merge step (5.6).
- [ ] **5.6** `gh pr merge --squash --delete-branch`, sync local main, run `/learn` if prompted.
- [ ] **5.7** **Post-merge follow-up** — once `skills.sh` re-scans the merged version, re-fetch the three scanner pages (agent-trust-hub, snyk, socket) and confirm the FAILs flip to PASS or move to documented residual-risk findings. If any real finding remains, open a follow-up spec.
