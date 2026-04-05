# Tasks: Spec 18 — peer-review Phase III (triage + re-scan)

## Phase 1: Triage layer

- [ ] Add Step 4e to SKILL.md (external CLI path only): spawn a Claude subagent with the triage prompt template from plan.md (including review mode and content type fields); pass normalized findings + collected Step 2 content (file contents for path targets, diff text for diff targets); subagent returns one `FINDING N: recommend` or `FINDING N: skip — reason` line per finding; split into `recommended` and `skipped` buckets; if triage output cannot be parsed, treat all findings as `recommend` and prepend "Triage unavailable — showing all findings."
- [ ] Rename current Step 4e ("Continue to Step 5") to Step 4f
- [ ] Update Step 5: add triage display logic
  - If `recommended` is empty: output "No issues recommended." + triage summary listing every skipped finding with its title and reason (`Triage filtered all N findings:\n- [title] — [reason]\n...`); stop; no apply prompt
  - Otherwise: number recommended findings sequentially (`1, 2, 3...`); number skipped findings with `S`-prefix (`S1, S2...`); display recommended findings in severity-grouped format; display triage-filtered section below; show modified apply prompt "Apply all recommended, include skipped by S-number, or skip? [all/1,2/1,S1/skip]"
- [ ] Update Step 5: `all` applies only recommended findings; explicitly state this
- [ ] Update Step 6 selection parsing: `all` applies only recommended findings; an explicit number (e.g., `1,S1`) applies that finding regardless of triage classification; `S`-prefixed numbers refer to skipped findings by their triage order; `skip` stops with no changes
- [ ] Confirm Step 4 Claude path is unchanged (no triage step added; no mention of triage in the claude- branch)

## Phase 2: Post-apply re-scan

- [ ] Update Step 6: after "Applied N finding(s)." — if at least one file was modified — output the re-scan offer and stop generating; resume only after user replies
- [ ] Add re-scan `y` path to Step 6: collect modified files' current content; build the **consistency mode** prompt (always consistency, regardless of original review mode); spawn a fresh Claude subagent (always Claude regardless of original `--model`); feed into Step 5; if no findings: "No new issues found in re-scan." and stop; **do not offer another re-scan after a re-scan cycle** — output "Applied N finding(s)." and stop
- [ ] Add re-scan `n` path to Step 6: stop
- [ ] Confirm no re-scan offer when user replied `skip` to the apply prompt

## Phase 3: SKILL.md update

- [ ] Verify Step 4 reads cleanly: the Claude path and external CLI path (with triage) are clearly delineated; triage is labeled "external CLI path only"
- [ ] Update the Notes section: add bullets for triage layer and post-apply re-scan per plan.md
- [ ] Bump `metadata.version` from `"1.1"` to `"1.2"` — do this once, in the first SKILL.md commit; do not bump again for follow-up commits on the same PR
- [ ] Run `npx cspell skills/peer-review/SKILL.md`; add any unknown words to `cspell.config.yaml`

## Phase 4: Evals

- [ ] Add `triage-skips-false-positive` eval to `evals/peer-review/evals.json`: prompt embeds a fixture with 2 normalized findings where one contradicts content already in the fixture (e.g., the prompt states "the reviewed content shows `npm install -g @github/copilot-cli` is the correct install hint" and finding 2 says "install hint is legacy — use `gh extension install`"); assertions: (1) finding 2 appears in "Triage filtered" section, not the apply list; (2) finding 1 is in the apply list
- [ ] Add `triage-all-skipped` eval: prompt embeds 2 findings that are both low-confidence opinions about style; assertions: (1) "No issues recommended." is shown; (2) no apply prompt is shown; (3) all skipped findings are listed in the triage summary with reasons
- [ ] Add `triage-not-on-claude-path` eval: prompt uses default `--model` (claude path); fixture: Claude subagent returns 2 findings; assertions: (1) no "Triage filtered" section appears; (2) apply prompt is standard form ("Apply all, select by number, or skip?"), not the "Apply all recommended" form
- [ ] Add `triage-user-includes-skipped` eval: prompt embeds 1 recommended finding (number 1) and 1 skipped finding (number S1); user reply is `S1`; assertion: the skipped finding is applied and the recommended finding is not (verifies S-prefix selection applies only the named finding)
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
- [ ] Add tests to `tests/peer-review/` covering triage routing: external CLI path triggers triage subagent; Claude path does not trigger triage; re-scan offer fires after apply; re-scan offer suppressed after skip; add a `classify_for_triage()` function (or equivalent) to `conftest.py` that maps `FINDING N: recommend/skip` lines to a dict — test cases can validate the parser in isolation
- [ ] Update PR description with new eval delta: run `git fetch origin && git log origin/main..HEAD --oneline`, compare against PR body, update with `gh pr edit` if new evals or behavior changes aren't reflected
- [ ] Run `uv run --with pytest pytest tests/` — confirm all tests pass
