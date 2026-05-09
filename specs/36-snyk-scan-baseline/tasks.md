# Spec 36: Tasks — Snyk-scan baseline + Security model template

## Phase 0: Worktree + branch setup

- [x] **0.1** Confirm worktree `agent-skills-security-baseline` exists at `../agent-skills-security-baseline` and is checked out on branch `security-baseline`. (`git worktree list`.)
- [x] **0.2** Stage `specs/36-snyk-scan-baseline/plan.md` and `tasks.md`.
- [ ] **0.3** *Optional* — run a fresh-context consistency pass over the spec docs before any deliverables land: `/peer-review specs/36-snyk-scan-baseline/`. Iteration cap 2. Apply valid findings inline.

---

## Phase 1: Capture baselines

For each of the four flagged skills, run the scanner once and capture the current finding set into a baseline file.

- [x] **1.1** Run `uvx snyk-agent-scan@latest --skills skills/peer-review/SKILL.md` and record the printed findings (confirmed locally: W011 high, W012 high). Write `evals/security/peer-review.baseline.json` per the schema in plan.md "Deliverable A".
- [x] **1.2** Same for `skills/ship-it/SKILL.md` — placeholder baseline drafted with `notes: "BASELINE NEEDS USER VERIFICATION"`. Refresh via `bash evals/security/scan.sh --update-baselines --confirm` once the harness lands.
- [x] **1.3** Same for `skills/pr-comments/SKILL.md` — placeholder baseline drafted (same caveat).
- [x] **1.4** Same for `skills/pr-human-guide/SKILL.md` — placeholder baseline drafted with empty findings (same caveat). Agent Trust Hub findings are addressed in spec 37, not this baseline.
- [x] **1.5** Validate every JSON file parses: `python3 -c 'import json; [json.load(open(f"evals/security/{s}.baseline.json")) for s in ["peer-review","ship-it","pr-comments","pr-human-guide"]]'` — passes.

---

## Phase 2: Build the harness

- [x] **2.1** Write `evals/security/scan.sh` per "Deliverable B". Pins scanner version explicitly inside the script (`SCANNER_PKG="snyk-agent-scan==0.5.1"`). Iterates the four flagged skills. Parses `[W### severity]:` lines. Compares against baseline. Exits 1 only on new findings or severity escalations.
- [x] **2.2** Script is idempotent — no state files written outside `${TMPDIR:-/private/tmp}`.
- [x] **2.3** `--scan-only` flag prints parsed scanner output without diffing.
- [x] **2.4** `--update-baselines` flag rewrites baselines; refuses without `--confirm`.
- [ ] **2.5** Locally: run `bash evals/security/scan.sh` — verify exits 0, then edit a baseline to delete one entry, rerun — verify exits 1. Revert. (Deferred — runs in CI and during the user's `--update-baselines --confirm` step in Phase 1.)
- [ ] **2.6** Document running with `bash evals/security/scan.sh` rather than relying on the executable bit (sandbox mode may not allow `chmod +x`).

---

## Phase 3: Pytest helper

- [x] **3.1** Create `tests/_helpers/argument_injection.py` exposing `ADVERSARIAL_ARGS` (numeric-arg adversarial values) and `ADVERSARIAL_TEXT_ARGS` (free-text adversarial values) per plan.md "Deliverable E". (No `__init__.py` — pytest auto-injects `tests/_helpers/` into `sys.path` in rootless mode so `from argument_injection import ...` works inside the directory; downstream skill tests in `tests/<skill>/` add the path explicitly via their conftest.py.)
- [x] **3.2** Add a sanity test `tests/_helpers/test_self.py` asserting both lists are non-empty and contain shell-metacharacter and unicode-homoglyph coverage.
- [x] **3.3** `uv run --with pytest pytest tests/_helpers/` — exits 0 with the sanity tests passing.

---

## Phase 4: Security model template

- [x] **4.1** Create `specs/36-snyk-scan-baseline/template.md` containing the canonical `## Security model` section structure: Threat model / Mitigations / Residual risks. Includes a worked example using peer-review's existing model so spec 37/38/39/40 authors have a concrete reference.

---

## Phase 5: CI workflow

- [x] **5.1** Create `.github/workflows/security-scan.yml` per "Deliverable D". Trigger: `pull_request` with `paths: [skills/**/SKILL.md, evals/security/**, .github/workflows/security-scan.yml]`. Job: `security-scan` on `ubuntu-latest`. Steps: checkout, set up Python 3.12, install `uv` via `astral-sh/setup-uv@v3`, restore `~/.cache/uv` cache keyed on the scanner version, run `bash evals/security/scan.sh`, print scan output on failure for debugging.
- [x] **5.2** Workflow named `security-scan` so reviewers see a clear status check name on PRs.

---

## Phase 6: Repo-level docs

- [x] **6.1** Create `evals/security/CLAUDE.md` per "Deliverable F". Uses the existing `# <Name>` + auto-load preamble pattern from `evals/CLAUDE.md` and `tests/CLAUDE.md`.
- [x] **6.2** Add `## Security scanning` section to root `CLAUDE.md` between `## Spell Checking` and `## Code Review`.
- [x] **6.3** Mirror the same section into `.github/copilot-instructions.md`.
- [x] **6.4** _Deferred — `README.md` has no repo-structure tree to update._ The current `README.md` is a skill-catalog table and prose, not a tree/ASCII layout. If one is added later, mirror `evals/security/` into it then; tracked here so plan.md and tasks.md stay aligned.
- [x] **6.5** `cspell.config.yaml` — add new tokens introduced by this PR alphabetically (`snyk`, `codegen`, `fullwidth`, `homoglyphs`, `parameterizes`, `subsetted`, `isoformat`).

---

## Phase 7: Verification

- [ ] **7.1** `bash evals/security/scan.sh` exits 0. (Runs in CI on the PR; deferred locally pending user-run baseline refresh in Phase 1.)
- [ ] **7.2** `bash evals/security/scan.sh --scan-only` prints parsed findings for all four skills. (Same as 7.1.)
- [x] **7.3** `python3 -c 'import json; [json.load(open(f"evals/security/{s}.baseline.json")) for s in ["peer-review","ship-it","pr-comments","pr-human-guide"]]'` exits 0.
- [x] **7.4** `uv run --with pytest pytest tests/_helpers/` exits 0 (5/5 sanity tests pass; full suite at 925/925).
- [x] **7.5** `npx cspell evals/security/*.md specs/36-snyk-scan-baseline/*.md CLAUDE.md .github/copilot-instructions.md tests/_helpers/*.py evals/security/scan.sh` clean.
- [x] **7.6** Re-read both `CLAUDE.md` and `.github/copilot-instructions.md`; the new `## Security scanning` section is equivalent in both.
- [ ] **7.7** Negative test: edit `evals/security/peer-review.baseline.json` to delete the W011 entry, rerun `bash evals/security/scan.sh` — exits 1 with the diff. Revert. (Deferred — depends on 7.1.)

---

## Phase 8: Peer review (bookend)

*Fresh-context consistency pass before ship.*

- [x] **8.1** Commit Phases 1–7 on branch `security-baseline`: `feat(security): scanner baseline + harness + Security model template (spec 36)`.
- [ ] **8.2** Run `/peer-review --branch security-baseline`. Apply valid findings. Loop until zero valid findings or iteration cap 4. Record per-iteration summary inline.

---

## Phase 9: Ship

- [x] **9.1** Push branch (`git push -u origin HEAD`), open PR.
- [ ] **9.2** Immediately invoke `/pr-comments {pr_number}` per project convention. Loop until clean.
- [ ] **9.3** Run `/pr-human-guide` to annotate the PR for human reviewers.
- [ ] **9.4** Verify CI green via `gh pr checks {pr_number}`. Confirm `security-scan` job passed.
- [ ] **9.5** A human reviewer must approve before merge — bot approval alone is not a substitute (per root `CLAUDE.md`).
- [ ] **9.6** `gh pr merge --squash --delete-branch`. Sync local main with `git status --porcelain` followed by `git reset --hard origin/main` (per root `CLAUDE.md` rule). Run `/learn` if prompted.
- [ ] **9.7** After spec 36 lands on main, the spec 37/38/39/40 worktrees can rebase to consume the harness.
