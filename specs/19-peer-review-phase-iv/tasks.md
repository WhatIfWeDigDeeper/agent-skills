# Peer-Review v1.4 — Tasks

## Implementation

- [ ] **Add staged/unstaged auto-detection to Step 2** — check `git diff --staged` and `git diff`; prompt user when both are present, auto-review unstaged when only unstaged exists, keep existing behavior when only staged or neither
- [ ] **Update help/usage block** — note that `--staged` explicit flag bypasses detection and always reviews staged only
- [ ] **Add noise-reduction bullets to diff mode prompt** — "Do NOT report" list + test coverage calibration note
- [ ] **Add noise-reduction bullets to consistency mode prompt** — "Do NOT report" list
- [ ] **Bump version to 1.4** in SKILL.md frontmatter

## Tests

- [ ] **Update `conftest.py`** — add staged/unstaged detection logic to `parse_arguments()` or `detect_mode()`
- [ ] **Add detection tests** — both staged+unstaged → prompt; unstaged only → auto-review; `--staged` explicit → no detection
- [ ] **Run tests** — `uv run --with pytest pytest tests/peer-review/` passes

## Evals

- [ ] **Add eval 21 to evals.json** — `both-staged-and-unstaged-prompt`: default target with both present; verify prompt shown and skill stops
- [ ] **Add eval 22 to evals.json** — `unstaged-only-auto-review`: no staged, unstaged present; verify auto-review with note
- [ ] **Add eval 23 to evals.json** — `staged-explicit-bypasses-detection`: `--staged` with both present; verify staged-only review, no prompt
- [ ] **Run eval 2** (with_skill + without_skill) — `consistency-mode-plan-tasks-mismatch`
- [ ] **Run evals 21, 22, 23** (with_skill + without_skill)
- [ ] **Grade all new/re-run evals**
- [ ] **Update benchmark.json** — add run entries for evals 2, 21, 22, 23; update metadata.evals_run and metadata.skill_version to 1.4
- [ ] **Update benchmark.md** — add per-eval sections for 21, 22, 23; backfill eval 2 section; update summary table
- [ ] **Update README.md Eval Δ column** — reflect new pass-rate delta

## Housekeeping

- [ ] **Run cspell** — `npx cspell skills/peer-review/SKILL.md`
- [ ] **Verify line count** — `wc -l skills/peer-review/SKILL.md` stays under 500
