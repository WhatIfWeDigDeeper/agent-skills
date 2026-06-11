# Spec 44: Tasks — peer-review Step 4d CLI headless-mode fixes

Implements `plan.md`. Edits target `skills/peer-review/SKILL.md` (v1.11 → v1.12). Anchors are
phrase-based; re-locate each block by its surrounding text since line numbers drift as edits land.

## Phase 1: Edits to `skills/peer-review/SKILL.md`

- [x] **1.1** Edit D (setup) — under `**4d. Execute and capture output:**`, immediately before the
  per-CLI branch, add `WORKDIR=$(mktemp -d "${TMPDIR:-/private/tmp}/peer-review-cwd.XXXXXX")`.
- [x] **1.2** Edit B (copilot) — replace the `For copilot:` if/else block with the `-p "$(cat
  "$PROMPT_FILE")"` + `cd "$WORKDIR"` form from plan.md "Edit B".
- [x] **1.3** Edit C (codex) — replace the `For codex (…)` heading prose and if/else block with the
  `codex exec --sandbox read-only --ask-for-approval never --skip-git-repo-check … -` form from
  plan.md "Edit C". Heading must drop `--no-auto-edit` and carry the **doc-derived, not locally
  verified** qualifier.
- [x] **1.4** Edit A (gemini) — replace the `For gemini (…)` if/else block with the short-`-p`-
  directive + `< "$PROMPT_FILE"` + `cd "$WORKDIR"` form from plan.md "Edit A". **Added `--skip-trust`**
  (discovered in 3.7): the neutral `$WORKDIR` is an untrusted folder and gemini otherwise reverts
  to interactive approval.
- [x] **1.5** Edit D (cleanup) — replace the lone `rm -f "$PROMPT_FILE"` cleanup at the end of
  Step 4d with `rm -f "$PROMPT_FILE"` + `rm -rf "$WORKDIR"`.
- [x] **1.6** Edit E (prose) — find the sentence beginning `Prompt content is passed via stdin
  redirection (copilot, gemini) or piping (codex)` and replace it with the corrected wording from
  plan.md "Edit E" (stdin for gemini/codex; copilot on argv; neutral `$WORKDIR` note).
- [x] **1.7** Edit F (Security model) — in the `## Security model` section: (a) rewrote the
  **Stdin transport for external CLIs** bullet to scope the guarantee to gemini + codex and name
  copilot as the exception; (b) added a **copilot argv exposure** bullet under **Residual risks**;
  (c) added a **Context isolation for external CLIs** mitigation bullet. `mktemp` / mode-600 /
  single-Bash-call rationale kept intact.
- [x] **1.8** Edit G — bump `metadata.version` from `"1.11"` to `"1.12"` in frontmatter.

---

## Phase 2: Tooling

- [x] **2.1** `npx cspell skills/peer-review/SKILL.md specs/44-peer-review-cli-headless-mode-fixes/*.md`
  — clean, no new tokens needed (new flags live in code fences; prose words `headless`/`argv`/
  `untrusted` already known). One jargon term flagged in a draft was reworded out.
- [x] **2.2** `uv run --with pytest pytest tests/` — 1136 passed, no regressions.

---

## Phase 3: Verification

- [x] **3.1** `rg -c 'cd "\$WORKDIR"' skills/peer-review/SKILL.md` → 6 matches. ✓
- [x] **3.2** `rg -c 'no-auto-edit' skills/peer-review/SKILL.md` → 0 matches. ✓
- [x] **3.3** `rg -n 'codex exec' skills/peer-review/SKILL.md` → present. ✓
- [x] **3.4** `rg -c 'WORKDIR=\$\(mktemp -d' skills/peer-review/SKILL.md` → 1 match. ✓
- [x] **3.5** `rg -c 'rm -rf "\$WORKDIR"' skills/peer-review/SKILL.md` → 1 match. ✓
- [x] **3.6** `rg -n '^  version:' skills/peer-review/SKILL.md` → `version: "1.12"`. ✓
- [x] **3.7** **gemini smoke test (installed, v0.45.2):** from a neutral empty dir,
  `gemini --approval-mode plan --skip-trust -p "Perform the diff review described in the input on stdin and return the findings now." < FILE`
  → returned `NO FINDINGS`, exit 0, **no hang**. The first run (without `--skip-trust`) surfaced
  the trust-gate finding and was added to Edit A (task 1.4). Confirms the #177 fix.
- [x] **3.8** **copilot smoke test (installed, v1.0.60):** from a neutral empty dir,
  `copilot --allow-all-tools --deny-tool='write' -p "Reply with exactly: OK"` → returned `OK`,
  exit 0, ~19.8k tokens (system-prompt overhead only — no repo ingestion, vs ~77k from repo
  root). Confirms the #176 fix (both the `-p` transport and the neutral-cwd context fix).
- [x] **3.9** **codex — unverified:** codex is not installed; the Edit C form is doc-derived
  (developers.openai.com/codex). Could not be smoke-tested — see Phase 5.1 follow-up. The
  documented form lands as written; no code change pending the test.
- [x] **3.10** Re-read Step 4d + the `## Security model` section end-to-end — phrase anchors held,
  the copilot residual-risk bullet matches Edit E's prose, and no CLI block was left on the old
  stdin-redirection form. ✓

---

## Phase 4: Ship

- [ ] **4.1** Branch `spec-44-peer-review-cli-headless-mode-fixes`. Commit the spec docs first
  (`spec(peer-review): v1.12 Step 4d headless-mode fix plan (#176, #177)`), then the SKILL.md
  edits (`feat(peer-review): v1.12 — headless-mode fixes for gemini/copilot/codex Step 4d (#176, #177)`).
- [ ] **4.2** **Bookend peer-review via copilot (live test of the fixed Step 4d copilot path; needs
  network — lift sandbox):** run `/peer-review skills/peer-review/SKILL.md --model copilot:gpt-5.4`.
  This exercises the new `-p "$(cat …)"` + neutral-`$WORKDIR` invocation end-to-end *and* gets a
  fresh-context review of the change. Apply valid findings (reply `all` to auto-approve), commit
  any edits before push. Record inline: did the copilot CLI run cleanly (no `No prompt provided`,
  no repo ingestion), and a one-line finding summary. (`gpt-5.4` is a free-form submodel value —
  the skill documents the `copilot[:submodel]` syntax but pins no specific model.)
- [ ] **4.3** **Bookend peer-review via gemini (live test of the fixed Step 4d gemini path; needs
  network — lift sandbox):** run `/peer-review skills/peer-review/SKILL.md --model gemini`. This
  exercises the new short-`-p`-directive + `< "$PROMPT_FILE"` invocation end-to-end. Apply valid
  findings (reply `all`), commit any edits before push. Record inline: did gemini complete without
  hanging, and a one-line finding summary. (Append a submodel if desired, e.g. `--model
  gemini:gemini-3-flash-preview`; plain `gemini` uses the default model.)
- [ ] **4.4** Push, open PR, immediately run `/pr-comments {pr_number}`.
- [ ] **4.5** Loop `/pr-comments` until no new bot feedback.
- [ ] **4.6** Run `/pr-human-guide` to annotate the PR for human reviewers.
- [ ] **4.7** Verify CI green (`gh pr checks {pr_number}`); a human reviews before merge.
- [ ] **4.8** `gh pr merge --squash --delete-branch`, sync local main, run `/learn` if prompted.
- [ ] **4.9** Close issues #176 and #177 referencing the merged PR.

---

## Phase 5: Follow-up

- [ ] **5.1** **codex verification (deferred from 3.9):** once `@openai/codex` is installable,
  smoke-test the Edit C form — `printf '%s' 'Reply with exactly: NO FINDINGS' | codex exec --sandbox read-only --ask-for-approval never --skip-git-repo-check -`
  from an empty dir. If the documented flags drifted, open a follow-up issue with the corrected
  invocation. Record the result (and any correction) here.
