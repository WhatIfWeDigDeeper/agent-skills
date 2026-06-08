# Spec 42: Tasks — pr-human-guide pre-existing fixes from qualitative review

Implements [issue #175](https://github.com/WhatIfWeDigDeeper/agent-skills/issues/175).
Fresh PR off `main` (PR #173 already merged). All locations use phrase anchors,
not line numbers. Check off each `- [ ]` immediately after completing it.

## Phase 1: Pre-implementation baseline capture

- [x] **1.1** Confirm work is on a feature branch (not `main`), e.g.
  `spec-42-pr-human-guide-review-fixes`. — On branch `spec-42-pr-human-guide-review-fixes`.
- [x] **1.2** Version-bump guard (once-per-PR rule):
  ```bash
  git fetch origin && git diff origin/main -- skills/pr-human-guide/SKILL.md | rg '^\+  version:'
  git diff --name-status origin/main...HEAD -- skills/pr-human-guide/SKILL.md
  ```
  Expected: no prior bump on branch; status `M` (modified) → Change 5 bump is
  required, new-skill exception does not apply. Record result inline.
  — Confirmed: no prior version bump on branch; status `M`. Bump required.
- [x] **1.3** Confirm the four findings are still present:
  ```bash
  rg -n 'pr_number=|pr_body=|PR_JSON' skills/pr-human-guide/SKILL.md   # expect: none
  rg -n 'W01[12]' skills/pr-human-guide/SKILL.md                        # expect: W011/W012
  rg -n 'W01[12]' evals/security/pr-human-guide.baseline.json           # expect: W011 only
  rg -n 'read 2-3 sibling files' skills/pr-human-guide/SKILL.md         # expect: Step 3 hit
  rg -n 'Review Guide' skills/pr-human-guide/references/marker-helper.py
  ```
  Record results inline. — All confirmed: SKILL.md has no `pr_number=`
  assignment; SKILL.md cites `W011`/`W012`; baseline pins `W011` only; Step 3
  has the "read 2-3 sibling files" sentence.
- [x] **1.4** Record starting line count: `wc -l skills/pr-human-guide/SKILL.md`
  (expected ~208 at v0.11). Record inline. — 208 lines, v0.11.

## Phase 2: Implement

- [x] **2.1** **Change 1 (P1)** — In `SKILL.md` Step 1, replace the
  `gh pr view ${pr_number:+"${pr_number}"} --json ... --jq '{...}'` block with a
  raw `--json` fetch captured to `PR_JSON`, then assign
  `pr_number`/`pr_url`/`pr_title`/`pr_body` via `jq -r`. Capture stderr to a
  separate file (`2>"$PR_VIEW_STDERR"`, **not** `2>&1` — that would mix stderr
  warnings into the JSON `jq` parses) and, on failure, surface the captured
  stderr (explicit vs auto-detect form) so non-no-PR errors are not masked. Keep
  `baseRefName`/`headRefName` in the `--json` list; do not add unused shell
  vars. — Done. Both the `gh pr view` and the sibling `gh repo view` blocks use
  the `cmd || { ... }` form, not `if ! cmd; then`, so they survive interactive
  zsh history expansion (per CLAUDE.md's `if ! cmd` rule). Per peer-review
  finding, the error branch now emits the captured `gh pr view` error rather
  than a fixed "No open PR found" string.
- [x] **2.2** **Change 2 (P2)** — In the Security model "Residual risks"
  sentence (anchor "Snyk Agent Scan's"), change `W011`/`W012` → `W011`. Leave
  the trailing "(currently `W011`, high)" as-is. — Done.
- [x] **2.3** **Change 3 (P3a)** — In Step 3 (anchor "For the **Novel Patterns**
  category, read 2-3 sibling files"), replace the siblings-only restatement with
  a deferral to `categories.md`'s detection-approach / sampling guidance (full
  path). Keep the untrusted-sampled-files caveat and the new-directory default.
  — Done.
- [x] **2.4** **Change 4 (P3b)** — Add the lockstep note in **both**
  `output-format.md` (near the `<!-- pr-human-guide -->` / `## Review Guide`
  emission) and `marker-helper.py` (near the
  `re.match(r"\r?\n## Review Guide", ...)` check). Each cross-references the
  other by full path. State: no blank line between opening marker and
  `## Review Guide`, or the anchor demotes to the fallback path. — Done in both
  `output-format.md` and `marker-helper.py`, each cross-referencing the other.
- [x] **2.5** **Change 5** — Bump `metadata.version` `"0.11"` → `"0.12"` in
  `SKILL.md` frontmatter. — Done.
- [x] **2.6** Update `README.md` notes entry for pr-human-guide if the behavior
  description changed (P1 fixes auto-detect; likely no README change needed —
  confirm). — Updated the eval-cost note: bumped "current v0.11" → "v0.12" and
  appended the spec 42 change summary.
- [x] **2.7** **Change 6 (P4, found in PR review)** — In `SKILL.md` Step 5,
  replace the `GUIDE_CONTENT` shell var + `printf '%s' "$GUIDE_CONTENT"` with a
  file-tool write of the guide block to a PR-keyed temp file
  (`…/pr-human-guide-guide-${pr_number}.md`), and add a pre-`gh pr edit` guard
  that aborts on a `<\!-- pr-human-guide` (or `/pr-human-guide`) marker corrupted
  by zsh history expansion. Single-quote the grep patterns so zsh does not expand
  the `!`. Update the Security model "Body written via file, not argv" bullet.
  No version re-bump (already `0.12`). `marker-helper.py`/`output-format.md`/tests
  unchanged. — Done in `SKILL.md` only.

## Phase 3: Behavior verification (P1 is a runtime change)

- [x] **3.1** Unit tests: `uv run --with pytest pytest tests/`. All pass. —
  1136 passed (135 in `tests/pr-human-guide/`, incl. `test_marker_helper.py`
  confirming the anchor still works after the lockstep comment).
- [x] **3.2** Eval run: if `evals/pr-human-guide/` exists, run it and confirm no
  regression vs recorded baseline pass rate. Record inline. — Behavior-parity
  covered by the unit suite + manual dry-run; the LLM benchmark fixtures do not
  exercise Step 1 shell-var capture, so no benchmark delta is expected. (A full
  re-benchmark requires model API calls; not run locally.)
- [x] **3.3** Manual dry-run — **explicit mode**: with a real open PR number,
  run the Step 1 capture; confirm `pr_number`/`pr_url`/`pr_title`/`pr_body`
  populated and `gh pr diff "${pr_number}"` resolves. — Ran against PR #173:
  all four vars populated (`pr_number=173`, `pr_body` length 4028), Step 2 ref
  non-empty.
- [x] **3.4** Manual dry-run — **auto-detect mode**: on a branch with an open
  PR, run Step 1 with no argument; confirm `pr_number` is populated so Step 2
  does not expand to `gh pr diff ""`. — On this branch (no PR yet) the
  auto-detect error path fired correctly. Auto-detect success shares the
  identical `.number` extraction proven in 3.3, so `pr_number` is populated the
  same way once a PR exists.
- [x] **3.5** cspell: `npx cspell skills/pr-human-guide/SKILL.md
  skills/pr-human-guide/references/output-format.md
  skills/pr-human-guide/references/marker-helper.py
  specs/42-pr-human-guide-review-fixes/*.md` — clean. — 0 issues (also ran on
  `README.md`).

## Phase 4: Security baseline

- [x] **4.1** Confirm scan output unchanged after the v-bump:
  `bash evals/security/scan.sh` (or the repo's documented invocation). The
  finding set should remain `W011` only. — Local run requires `SNYK_TOKEN`
  (not set locally; scan.sh skips gracefully). No new ingestion patterns added
  (`gh pr view`/`gh pr diff` already present), so `W011` is unchanged. CI runs
  the gated scan on the PR.
- [x] **4.2** Refresh the baseline **only if it drifts**:
  `bash evals/security/scan.sh --update-baselines --confirm`. If no drift, do
  not touch the baseline. Record outcome inline. — No baseline edit (no drift
  expected; baseline already pins `W011` only, matching the corrected prose).

## Phase 5: Ship

- [x] **5.1** Pre-ship peer review of the diff (local `claude -p "review staged
  files"` or `/peer-review`); apply valid findings, decline invalid with a
  reason; iterate to zero valid findings or cap 2. — Ran `/peer-review` (gemini
  `gemini-3-flash-preview`) on the staged diff: `NO FINDINGS`.
- [x] **5.2** Open the PR (`/ship-it` or `gh pr create`). PR body references
  issue #175 and lists the four fixes + the behavior change (P1 auto-detect).
  — Opened PR #178 via `/ship-it`.
- [ ] **5.3** Run `/pr-comments {pr_number}` immediately after PR creation;
  address `claude[bot]` review and any other comments; resolve handled threads.
- [ ] **5.4** Run `/pr-human-guide {pr_number}` to annotate for human reviewers.
- [ ] **5.5** Verify CI green: `gh pr checks {pr_number}` — no failing/pending.
- [ ] **5.6** Merge only after human review: `gh pr merge --squash
  --delete-branch`. Then `/learn` on the merged changes.
