# Spec 44: peer-review — Step 4d CLI headless-mode fixes (issues #176, #177)

## Problem

Three of the four external-CLI invocations in `peer-review` Step 4d are broken against
current CLI versions. The skill (v1.11) was written for older CLIs that read a prompt from
stdin in non-interactive mode; the installed CLIs no longer do.

| CLI | Version | Symptom | Source |
|-----|---------|---------|--------|
| gemini | 0.45.2 (confirmed local) | `gemini --approval-mode plan < FILE` **hangs indefinitely** — current gemini defaults to interactive mode; feeding the prompt via stdin alone drops into a TUI waiting on terminal input that never arrives. | #177 |
| copilot | 1.0.60 (confirmed local) | `copilot … < FILE` prints `No prompt provided. Run in an interactive terminal or provide a prompt with -p or via standard in.` — stdin redirection is ignored non-interactively. Separately, run from the repo root copilot ingested ~77k tokens of unrelated repo context before reviewing. | #176 |
| codex | not installed (docs research) | `cat FILE \| codex --no-auto-edit` is **doubly broken** — `--no-auto-edit` was removed in the Rust rewrite, and without the `exec` subcommand `codex` drops into an interactive TUI (same hang class as gemini). | #177 note |

This touches a deliberate security mitigation. Step 4d's **stdin transport** keeps the prompt
(diff / PR body / any secrets that slipped past the pre-flight scan) off the process command
line, where `ps` / `/proc/<pid>/cmdline` would expose it to other local users. The fix must
preserve that property wherever the CLI allows it, and document the residual risk where it
does not.

## Research findings (codex)

codex is not installable in the authoring environment, so the codex path was established from
OpenAI's official docs (developers.openai.com/codex, latest npm `@openai/codex` 0.139.0):

- **Headless subcommand:** `codex exec` (alias `codex e`) runs without the interactive TUI.
- **Stdin sentinel:** `codex exec -` — the `-` reads the *entire prompt from stdin*, so the
  bulk untrusted content stays off argv. **This preserves stdin transport.**
- **Read-only:** `codex exec` defaults to `--sandbox read-only`; pair with
  `--ask-for-approval never` so it does not block waiting for approval.
- **Outside a git repo:** `--skip-git-repo-check` lets `codex exec` run from the empty neutral
  working directory.
- `-m`/`--model` is unchanged; `--no-auto-edit` no longer exists.

## Decisions (settled with user)

| Topic | Decision |
|-------|----------|
| **gemini transport** | Add a short fixed `-p` directive; keep the bulk prompt on stdin (`< "$PROMPT_FILE"`). gemini *appends stdin to the `-p` prompt*, so **stdin transport is fully preserved** — only a short fixed directive is on argv. |
| **copilot transport** | Switch to `-p "$(cat "$PROMPT_FILE")"` (argv). The current copilot CLI does not honor stdin non-interactively. Drop the stdin-transport claim for copilot; document argv exposure as a residual risk; rely on the existing pre-flight secret scan (Step 4b). |
| **codex transport** | Apply the documented `codex exec … -` form (stdin transport preserved via the `-` sentinel). Mark doc-derived / locally-unverified; smoke-test once codex is installable. |
| **External-CLI cwd** | Run every external CLI from a freshly-created empty temp dir so it reviews only the supplied prompt rather than re-scanning the repo (~77k tokens for copilot at repo root). |

## Design

All edits target `skills/peer-review/SKILL.md` (currently v1.11, 692 lines, no reference files).
Anchors are phrase-based — line numbers will drift as edits land.

### Edit A — gemini headless fix (#177)

Anchor: the gemini block under `**4d. Execute and capture output:**`
(`For gemini (\`--approval-mode plan\` enables read-only mode):`). Replace the if/else block:

```bash
CLI_RC=0
if [ -n "$SUBMODEL" ]; then
  REVIEW_OUTPUT=$(cd "$WORKDIR" && gemini --approval-mode plan --skip-trust -m "$SUBMODEL" \
    -p "Perform the diff review described in the input on stdin and return the findings now." \
    < "$PROMPT_FILE" 2>&1) || CLI_RC=$?
else
  REVIEW_OUTPUT=$(cd "$WORKDIR" && gemini --approval-mode plan --skip-trust \
    -p "Perform the diff review described in the input on stdin and return the findings now." \
    < "$PROMPT_FILE" 2>&1) || CLI_RC=$?
fi
```

**`--skip-trust` is required (discovered during implementation smoke-testing).** Edit D runs
gemini from the neutral empty `$WORKDIR`, which gemini treats as an *untrusted folder*: without
`--skip-trust` it prints `Gemini CLI is not running in a trusted directory…`, silently overrides
`--approval-mode plan` back to `default`, and reverts to interactive approval. `--skip-trust`
(valid in v0.45.2) lets it run headless from the temp dir. copilot and codex have no equivalent
trust gate.

### Edit B — copilot headless fix + accepted argv tradeoff (#176)

Anchor: the copilot block (`For copilot:`). Replace the if/else block:

```bash
CLI_RC=0
if [ -n "$SUBMODEL" ]; then
  REVIEW_OUTPUT=$(cd "$WORKDIR" && copilot --allow-all-tools --deny-tool='write' \
    --model "$SUBMODEL" -p "$(cat "$PROMPT_FILE")" 2>&1) || CLI_RC=$?
else
  REVIEW_OUTPUT=$(cd "$WORKDIR" && copilot --allow-all-tools --deny-tool='write' \
    -p "$(cat "$PROMPT_FILE")" 2>&1) || CLI_RC=$?
fi
```

### Edit C — codex headless fix, doc-derived (#177 codex regression note)

Anchor: the codex block and its heading
(`For codex (\`--no-auto-edit\` suppresses file writes; …):`). Update the heading (the flag no
longer exists) and replace the if/else block:

New heading prose: `For codex (\`codex exec\` runs headless; \`--sandbox read-only\` prevents
writes; the trailing \`-\` reads the prompt from stdin — **doc-derived from
developers.openai.com/codex; not verified against a locally installed codex**):`

```bash
CLI_RC=0
if [ -n "$SUBMODEL" ]; then
  REVIEW_OUTPUT=$(cd "$WORKDIR" && cat "$PROMPT_FILE" \
    | codex exec --sandbox read-only --ask-for-approval never --skip-git-repo-check --model "$SUBMODEL" - 2>&1) || CLI_RC=$?
else
  REVIEW_OUTPUT=$(cd "$WORKDIR" && cat "$PROMPT_FILE" \
    | codex exec --sandbox read-only --ask-for-approval never --skip-git-repo-check - 2>&1) || CLI_RC=$?
fi
```

`cd "$WORKDIR" && cat … | codex …` parses as `cd && (cat | codex)` (`&&` binds looser than `|`),
so the pipeline runs in the neutral dir as intended; `|| CLI_RC=$?` captures the pipeline status
(last command = codex).

### Edit D — neutral working directory for all external CLIs

In Step 4d, immediately before the CLI branch, create an empty temp dir; clean it up alongside
`$PROMPT_FILE` at the end of the step. Both create→use→cleanup stay inside the single Bash tool
call already required for Steps 4c+4d.

Add before the branch (guard creation so `$PROMPT_FILE` is still cleaned up and `cd "$WORKDIR"`
never falls back to the current dir if `mktemp -d` fails):
```bash
WORKDIR=$(mktemp -d "${TMPDIR:-/private/tmp}/peer-review-cwd.XXXXXX") || { rm -f "$PROMPT_FILE"; echo "peer-review: could not create neutral working directory; aborting." >&2; exit 1; }
```

Replace the lone cleanup `rm -f "$PROMPT_FILE"` with (guard the `rm -rf` so an unset/empty
`$WORKDIR` can never expand to an unintended path):
```bash
rm -f "$PROMPT_FILE"
if [ -n "${WORKDIR:-}" ]; then rm -rf "$WORKDIR"; fi
```

The `$(cd "$WORKDIR" && …)` subshell isolates the cwd change to each capture and does not affect
the outer shell — `$PROMPT_FILE` is an absolute path and reads fine from any cwd.

### Edit E — Step 4c/4d prose

The sentence beginning `Prompt content is passed via stdin redirection (copilot, gemini) or
piping (codex)…` is now wrong for copilot. Replace with wording to the effect of:

> Prompt content is passed via stdin for gemini (appended to a short fixed `-p` directive) and
> codex (`codex exec -` reads stdin), so it never appears on those CLIs' command lines. copilot's
> current CLI does not honor stdin non-interactively, so its prompt is passed via `-p` on argv —
> see **Residual risks**. All external CLIs run from a neutral empty `$WORKDIR` so they review
> only the supplied prompt, not the repository.

### Edit F — Security model section

Anchor: the `## Security model` section (the **Stdin transport for external CLIs** mitigation
bullet and the **Residual risks** sub-list).

1. Rewrite the **Stdin transport for external CLIs** bullet: stdin transport holds for **gemini
   and codex** (the prompt stays off argv — gemini appends stdin to a short `-p` directive,
   codex reads stdin via the `-` sentinel); **copilot is the exception** — its current CLI
   ignores stdin non-interactively, so its prompt is passed via `-p` on the command line. Keep
   the existing `mktemp` / mode-600 / single-Bash-call temp-file rationale unchanged.
2. Add a **Residual risks** bullet — **copilot argv exposure**: copilot ≥1.0.x does not honor
   stdin non-interactively, so its prompt is visible to other local users via `ps` /
   `/proc/<pid>/cmdline`; the pre-flight secret scan (Step 4b) is the mitigating control; gemini
   and codex retain stdin transport.
3. Add a brief **context isolation** note (mitigation or residual-risk list, implementer's
   choice): external CLIs run from an empty cwd, which also reduces incidental repo-file exposure
   to the third-party vendor.

### Edit G — version bump

`metadata.version: "1.11"` → `"1.12"` (exactly one bump for the PR).

### No change needed

The model/submodel table (`| copilot | copilot | --model SUBMODEL |`, `| codex | codex | --model
SUBMODEL |`, `| gemini | gemini | -m SUBMODEL |`) is unchanged — binary names and submodel flags
still match. Only the invocation forms change.

## Files to modify

| File | Change |
|------|--------|
| `skills/peer-review/SKILL.md` | Edits A–G |
| `cspell.config.yaml` | Add any newly-flagged prose tokens in alphabetical position (most new flags live in code fences and are ignored by cspell). |
| `README.md` | Only if the v1.10 **Security model** summary bullet needs a tweak to mention the copilot argv residual risk; surface API (triggers/args/options) is unchanged. Decide during implementation. |
| `specs/44-peer-review-cli-headless-mode-fixes/{plan,tasks}.md` | The spec docs themselves, committed on the branch. |

## Verification

CLI smoke tests need outbound network — lift any sandbox restrictions (in Claude Code:
`dangerouslyDisableSandbox: true`).

1. **gemini (installed, v0.45.2 — DONE):** write `Reply with exactly: NO FINDINGS` to a temp file,
   then `gemini --approval-mode plan --skip-trust -p "Perform the diff review described in the input on stdin and return the findings now." < FILE` from an empty dir — completes and returns `NO FINDINGS`, **no hang**. (First run without `--skip-trust` surfaced the trust-gate finding above.)
2. **copilot (installed, v1.0.60 — DONE):** `copilot --allow-all-tools --deny-tool='write' -p "Reply with exactly: OK"` from an empty dir — returned `OK` promptly, ~19.8k tokens (system-prompt overhead only; no repo ingestion).
3. **codex (not installed):** cannot run; leave Edit C marked doc-derived/unverified with a
   follow-up task to smoke-test `codex exec … -` once installable.
4. `rg -n 'cd "\$WORKDIR"' skills/peer-review/SKILL.md` → 6 matches (copilot/codex/gemini × if/else).
5. `rg -n 'no-auto-edit' skills/peer-review/SKILL.md` → no matches (legacy flag gone).
6. `rg -n 'codex exec' skills/peer-review/SKILL.md` → present.
7. `rg -n 'WORKDIR=\$\(mktemp -d' skills/peer-review/SKILL.md` → exactly 1 match (Edit D).
8. `rg -n '^  version:' skills/peer-review/SKILL.md` → `version: "1.12"`.
9. `npx cspell skills/peer-review/SKILL.md specs/44-peer-review-cli-headless-mode-fixes/*.md` — clean.
10. `uv run --with pytest pytest tests/` — no regressions.
11. Re-read Step 4d + the Security model section end-to-end after all edits to confirm phrase
    anchors held and the copilot residual-risk bullet is internally consistent with Edit E's prose.

## Shipping

1. Branch `spec-44-peer-review-cli-headless-mode-fixes`; commit the spec docs first, then the
   SKILL.md edits.
2. `feat(peer-review): v1.12 — headless-mode fixes for gemini/copilot/codex Step 4d (#176, #177)`.
3. **Bookend peer-review (pre-PR, exercises the fixed Step 4d paths against real CLIs):** run
   `/peer-review skills/peer-review/SKILL.md --model copilot:gpt-5.4`, then `… --model gemini`.
   Each run is both a fresh-context review of the change and a live test of the newly-fixed
   copilot (`-p`) and gemini (`-p` + stdin) invocations. Apply valid findings and commit before
   push. Needs network — lift sandbox restrictions. (codex is not installed, so it cannot be
   exercised here — see Phase 5 follow-up.)
4. Push, open PR, immediately run `/pr-comments {pr_number}`; after bot review settles run
   `/pr-human-guide`; verify CI green (`gh pr checks`); a human reviews before merge.
5. `gh pr merge --squash --delete-branch`, sync local main, run `/learn` if prompted.
6. Close issues #176 and #177 referencing the PR.

## Out of scope

- **Runtime CLI-capability detection for copilot** (option C in #176) — user chose the simpler
  baked-in `-p` decision.
- **Reworking the secret-scan patterns or the triage layer** — unchanged; the secret scan is the
  mitigating control the copilot argv tradeoff leans on, but its content is not modified here.
- **Eval changes** — the existing `--model copilot` evals mock the CLI response and do not
  exercise the invocation path; they stay valid. Propose a new eval only if trivial.
- **Pinning CLI versions in the skill** — covered by the existing "Third-party CLI provenance"
  mitigation; no automated enforcement added.
