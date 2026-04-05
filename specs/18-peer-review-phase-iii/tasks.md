# Tasks: Spec 18 — peer-review Phase III (triage + re-scan)

## Phase 1: Triage layer

- [ ] Add Step 4e to SKILL.md (external CLI path only): spawn a Claude subagent with the triage prompt + normalized findings + reviewed file contents; the subagent returns one `FINDING N: recommend` or `FINDING N: skip — reason` line per finding; split results into `recommended` and `skipped` buckets
- [ ] Add the triage prompt template to SKILL.md Step 4e (exact text from plan.md)
- [ ] Rename current Step 4e ("Continue to Step 5") to Step 4f
- [ ] Update Step 5: add triage display logic
  - If `recommended` is empty: output "No issues recommended." + triage summary (`Triage filtered all N findings: ...`); stop; no apply prompt
  - Otherwise: number all findings globally (recommended in order, then skipped continuing the sequence); display recommended findings in severity-grouped format; display triage-filtered section below; show modified apply prompt "Apply all recommended, select by number (include skipped by their number), or skip? [all/1,2/1,3/skip]"
- [ ] Update Step 5: `all` applies only recommended findings; explicitly state this
- [ ] Confirm Step 4 Claude path is unchanged (no triage step added; no mention of triage in the claude- branch)

## Phase 2: Post-apply re-scan

- [ ] Update Step 6: after "Applied N finding(s)." — if at least one file was modified — output the re-scan offer and stop generating; resume only after user replies
- [ ] Add re-scan `y` path to Step 6: collect modified files' current content; build the same mode prompt (diff/spec/consistency from original target); spawn a fresh Claude subagent (always Claude regardless of original `--model`); feed into Step 5; if no findings: "No new issues found in re-scan." and stop
- [ ] Add re-scan `n` path to Step 6: stop
- [ ] Confirm no re-scan offer when user replied `skip` to the apply prompt

## Phase 3: SKILL.md update

- [ ] Verify Step 4 reads cleanly: the Claude path and external CLI path (with triage) are clearly delineated; triage is labeled "external CLI path only"
- [ ] Update the Notes section: add bullets for triage layer and post-apply re-scan per plan.md
- [ ] Bump `metadata.version` from `"1.1"` to `"1.2"` — do this once, in the first SKILL.md commit; do not bump again for follow-up commits on the same PR
- [ ] Run `npx cspell skills/peer-review/SKILL.md`; add any unknown words to `cspell.config.yaml`

## Phase 4: Evals

- [ ] Add `triage-skips-false-positive` eval to `evals/peer-review/evals.json`: prompt embeds a fixture with 2 normalized findings where one contradicts content already in the fixture (e.g., the prompt states "the reviewed content shows `npm install -g @github/copilot-cli` is the correct install hint" and finding 2 says "install hint is legacy — use `gh extension install`"); assertions: (1) finding 2 appears in "Triage filtered" section, not the apply list; (2) finding 1 is in the apply list
- [ ] Add `triage-all-skipped` eval: prompt embeds 2 findings that are both low-confidence opinions about style; assertions: (1) "No issues recommended." is shown; (2) no apply prompt is shown; (3) at least one finding is listed in the triage summary
- [ ] Add `triage-not-on-claude-path` eval: prompt uses default `--model` (claude path); fixture: Claude subagent returns 2 findings; assertions: (1) no "Triage filtered" section appears; (2) apply prompt is standard form ("Apply all, select by number, or skip?"), not the "Apply all recommended" form
- [ ] Add `triage-user-includes-skipped` eval: prompt embeds 1 recommended finding and 1 skipped finding; user reply includes the skipped finding's number; assertion: both findings are applied (the skipped one is applied despite triage classification)
- [ ] Add `rescan-offered-after-apply` eval: prompt specifies that a finding was applied to a file; assertions: (1) "Applied N finding(s)." is shown; (2) the re-scan offer ("Re-scan modified files for new issues?") is shown
- [ ] Add `rescan-not-offered-after-skip` eval: user replies `skip` to the apply prompt; assertions: (1) "Skipped N findings. No changes made." is shown; (2) no re-scan offer is shown
- [ ] Run all 6 new evals with_skill and without_skill; spawn subagents with `mode: "auto"`
- [ ] Grade results; update `evals/peer-review/benchmark.json` with new runs; update `metadata.evals_run` and `metadata.skill_version`
- [ ] Each new eval must have at least one assertion that fails without_skill — if any eval is non-discriminating, add a note in `benchmark.json` explaining why
- [ ] Update `benchmark.md`: add per-eval sections for all new evals; update token-count denominator in the "Token statistics" sentence — M increases by 6; update both M and 2×M
- [ ] Update `README.md` Eval Δ column to reflect the new delta

## Phase 5: Documentation and README

- [ ] Update `README.md` Skill Notes for `peer-review`: add description of triage layer and post-apply re-scan to the multi-LLM routing note
- [ ] Update Eval cost bullet with updated token/time stats from the new `benchmark.md` Summary table
- [ ] Add tests to `tests/peer-review/` covering triage routing: external CLI path triggers triage subagent; Claude path does not trigger triage; re-scan offer fires after apply; re-scan offer suppressed after skip
- [ ] Run `uv run --with pytest pytest tests/` — confirm all tests pass
