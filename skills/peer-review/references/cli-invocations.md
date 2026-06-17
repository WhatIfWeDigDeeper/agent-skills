# peer-review — external-CLI invocation + output normalization (Steps 4c–4e)

This is the external-CLI executable path (copilot / codex / gemini). SKILL.md
Step 4c keeps the security rationale (the stdin-vs-argv explanation, the
single-call invariant, the "Why `mktemp`" note, and the explicit-cleanup-not-`trap`
note); SKILL.md Step 4 keeps the which-CLI dispatch table that sets `$SUBMODEL`
and selects the binary. **Run the entire write → invoke → cleanup block in a
single Bash tool call** — `$PROMPT_FILE` is a subshell-scoped variable created by
the write below and consumed/cleaned by the invocation; splitting them strands
the temp file or makes the CLI read `/dev/null`. Step 4e (parse) is non-shell and
runs in the assistant afterward, from the captured `REVIEW_OUTPUT`.

## 4c — write prompt to temp file

```bash
PROMPT_FILE=$(mktemp "${TMPDIR:-/private/tmp}/peer-review-prompt.XXXXXX")
chmod 600 "$PROMPT_FILE"
printf '%s' "$PROMPT" > "$PROMPT_FILE"
```

## 4d — execute and capture output

Each CLI invocation captures its exit status in `CLI_RC` so non-zero exits (CLI warnings, parse errors, network failures) do not abort the bash block before the temp-file cleanup runs. The `|| CLI_RC=$?` form is `set -e`-safe — without it, a non-zero CLI exit would propagate out of the `$( … )` assignment and skip the unconditional `rm -f` below, leaving the prompt file (which may contain unredacted diff content) on disk.

First, create a neutral empty working directory and run the selected CLI from inside it, so the external CLI reviews only the supplied prompt rather than ingesting the repository as agent context. The `cd` happens inside the `$( … )` subshell, so it does not affect the outer shell; `$PROMPT_FILE` is an absolute path and reads fine from any cwd. Guard the `mktemp -d` so a failure (un-writable `$TMPDIR`, disk full) removes `$PROMPT_FILE` (which may hold unredacted diff content / secrets) and aborts with a clear error — without the guard, a failed `mktemp -d` would leave `WORKDIR` empty, and the later `cd "$WORKDIR"` would become `cd ""` (a no-op that keeps the CLI in the repo root, defeating the neutral-cwd isolation); under `set -e` the failed assignment would instead abort the block before the cleanup, stranding `$PROMPT_FILE` on disk:
```bash
WORKDIR=$(mktemp -d "${TMPDIR:-/private/tmp}/peer-review-cwd.XXXXXX") || { rm -f "$PROMPT_FILE"; echo "peer-review: could not create neutral working directory; aborting." >&2; exit 1; }
```

For copilot (passes the prompt via `-p` on argv — copilot's current CLI does not honor stdin in non-interactive mode; see the Security model's Residual risks):
```bash
CLI_RC=0
if [ -n "$SUBMODEL" ]; then
  REVIEW_OUTPUT=$({ cd "$WORKDIR" && copilot --allow-all-tools --deny-tool='write' --model "$SUBMODEL" -p "$(cat "$PROMPT_FILE")"; } 2>&1) || CLI_RC=$?
else
  REVIEW_OUTPUT=$({ cd "$WORKDIR" && copilot --allow-all-tools --deny-tool='write' -p "$(cat "$PROMPT_FILE")"; } 2>&1) || CLI_RC=$?
fi
```

For codex (`codex exec` runs headless; `--sandbox read-only` prevents writes; `--ask-for-approval never` stops it blocking on approval; `--skip-git-repo-check` allows running from the empty `$WORKDIR`; the trailing `-` reads the prompt from stdin, so the prompt stays off argv — **doc-derived from developers.openai.com/codex; not verified against a locally installed codex**):
```bash
CLI_RC=0
if [ -n "$SUBMODEL" ]; then
  REVIEW_OUTPUT=$({ cd "$WORKDIR" && codex exec --sandbox read-only --ask-for-approval never --skip-git-repo-check --model "$SUBMODEL" - < "$PROMPT_FILE"; } 2>&1) || CLI_RC=$?
else
  REVIEW_OUTPUT=$({ cd "$WORKDIR" && codex exec --sandbox read-only --ask-for-approval never --skip-git-repo-check - < "$PROMPT_FILE"; } 2>&1) || CLI_RC=$?
fi
```

For gemini (`--approval-mode plan` enables read-only mode; `-p` triggers headless mode — the current gemini CLI hangs in an interactive TUI without it; gemini *appends stdin to the `-p` prompt*, so the bulk prompt stays on stdin and only a short fixed directive is on argv; `--skip-trust` is required because the neutral `$WORKDIR` is an untrusted folder — without it gemini refuses to run headless and reverts to interactive approval):
```bash
CLI_RC=0
if [ -n "$SUBMODEL" ]; then
  REVIEW_OUTPUT=$({ cd "$WORKDIR" && gemini --approval-mode plan --skip-trust -m "$SUBMODEL" -p "Perform the diff review described in the input on stdin and return the findings now." < "$PROMPT_FILE"; } 2>&1) || CLI_RC=$?
else
  REVIEW_OUTPUT=$({ cd "$WORKDIR" && gemini --approval-mode plan --skip-trust -p "Perform the diff review described in the input on stdin and return the findings now." < "$PROMPT_FILE"; } 2>&1) || CLI_RC=$?
fi
```

After the CLI call returns (success or failure), clean up the temp file and the neutral working directory unconditionally — the `|| CLI_RC=$?` capture above guarantees control reaches this line even when the CLI exited non-zero:
```bash
rm -f "$PROMPT_FILE"
if [ -n "${WORKDIR:-}" ]; then rm -rf "$WORKDIR"; fi
```

`CLI_RC` is a bash variable scoped to the Bash tool call that ran Step 4d — it does not persist into the prose of Step 4e (the assistant parses `REVIEW_OUTPUT` itself; bash variables go out of scope when the Bash call ends). If you want to act on the exit status before parsing, do so **within the same Bash tool call** as Step 4d — for example, append a sentinel to the captured output so Step 4e can still see it:

```bash
if [ "$CLI_RC" -ne 0 ]; then
  REVIEW_OUTPUT="[CLI exited $CLI_RC]"$'\n'"$REVIEW_OUTPUT"
fi
```

The marker survives into Step 4e's parsing input (which is the assistant's reading of `REVIEW_OUTPUT`), so the parser can short-circuit to the raw-output fallback path on `CLI exited <nonzero>` plus malformed body.

## 4e — parse output → normalized findings

For copilot: output is JSON with schema `{ summary, overall_risk, findings: [{ severity, file, title, details, suggested_fix }] }`. Extract `findings[]`; map `details` → problem, `suggested_fix` → fix. Apply severity normalization below. If `findings` is empty, treat as `NO FINDINGS`. If JSON is malformed, fall through to raw-output fallback.

For codex and gemini: output is markdown or plain text. First check if output is exactly `NO FINDINGS` — if so, treat as no issues. Otherwise parse severity from lines matching patterns like `[HIGH]`, `**Critical**`, `severity: high` (case-insensitive). Extract title, file, problem, and fix from surrounding lines. If no structured severity pattern is found, present the full output as a single `major` finding.

If parsing fails for any CLI: output raw text with the prefix "Could not parse structured findings; showing raw output." Then stop — this is a terminal output. Do not proceed to triage (Step 4f) or apply (Step 6); the raw text is presented directly to the user, who can re-run the skill or invoke the CLI manually if they need structured findings.

**Severity normalization** (apply case-insensitively for all CLIs):

| Input severity | Normalized |
|---------------|-----------|
| `high` / `error` / `critical` | `critical` |
| `medium` / `warning` / `major` | `major` |
| `low` / `info` / `note` / `minor` | `minor` |
