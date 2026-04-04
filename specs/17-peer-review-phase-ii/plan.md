# Spec 17: peer-review — Phase II Multi-LLM routing (v1.0 → v1.1)

## Problem

Phase I of the `peer-review` skill (v1.0) uses a Claude subagent as the reviewer. `--model copilot`, `--model codex`, and `--model gemini` are documented in the help text and Notes but not implemented — passing them silently falls back to the Claude subagent. The value proposition of multi-LLM routing is getting a non-Claude perspective or using a specific model the author has access to. That deferred capability is the scope of Phase II.

Current state: `skills/peer-review/SKILL.md` v1.0, 244 lines.

---

## Design

### Overview

When `--model` starts with `claude-` (including the default `claude-opus-4-6`), the skill behaves identically to Phase I: spawn a Claude subagent.

When `--model` is `copilot[:<submodel>]`, `codex`, or `gemini[:<submodel>]`, Step 4 of the skill routes to an external CLI instead of spawning a subagent. Steps 1–3 (parse, collect, build prompt) and Steps 5–6 (present, apply) are unchanged.

### Model routing table

| `--model` value | CLI binary | Sub-model flag |
|----------------|-----------|---------------|
| `copilot` | `copilot` | `-m MODEL` |
| `copilot:gpt-4o-mini` | `copilot` | `-m gpt-4o-mini` |
| `codex` | `codex` | `--model MODEL` (if sub-model provided) |
| `gemini` | `gemini` | `--model MODEL` (if sub-model provided) |
| `gemini:gemini-2.0-flash` | `gemini` | `--model gemini-2.0-flash` |

### Step 4 branch: external CLI path

```
4a. Check binary availability
    which <binary> || error "MODEL CLI not found. Install with: <install hint>"

4b. Build the shell invocation
    - Write the review prompt (template from Step 3 + collected content) to a temp file:
        PROMPT_FILE=$(mktemp "${TMPDIR:-/tmp}/peer-review-prompt.XXXXXX")
        printf '%s' "$PROMPT" > "$PROMPT_FILE"
      This avoids shell metacharacter injection from diff/PR/commit content passed as a CLI argument.
      Use $TMPDIR (not /tmp directly) per sandbox rules.
    - Add sub-model flag if provided
    - For copilot: pass prompt via -p "$(cat $PROMPT_FILE)" or --prompt-file if supported; restrict tool access (--deny-tool='write')
    - For codex: pass --no-auto-edit or equivalent read-only flag (TBD from research); pass prompt via stdin or file
    - For gemini: pass read-only constraints (TBD from research); pass prompt via stdin or file

4c. Execute and capture output
    REVIEW_OUTPUT=$(<binary> <prompt-flag> "$(cat "$PROMPT_FILE")" [<submodel-flag>] [<read-only-flag>])
    # Example for copilot: REVIEW_OUTPUT=$(copilot -p "$(cat "$PROMPT_FILE")" [-m SUBMODEL] [--deny-tool='write'])
    # Exact flags differ per CLI — see per-CLI integration notes below

4d. Parse output → severity buckets
    - Each CLI emits different formats (see per-CLI sections below)
    - Normalize to the standard findings structure (critical/major/minor + title/file/location/problem/fix)
    - If parsing fails: show raw output + "Could not parse structured findings; showing raw output."

4e. Continue to Step 5 (present findings) with normalized findings
```

### Severity normalization

| Input severity | Normalized |
|---------------|-----------|
| `high` / `error` / `critical` | `critical` |
| `medium` / `warning` / `major` | `major` |
| `low` / `info` / `note` / `minor` | `minor` |

Apply this table regardless of CLI source. Case-insensitive match.

### Install hints per CLI

| CLI | Install hint |
|----|-------------|
| copilot | `npm install -g @github/copilot-cli` or via the GitHub Copilot VS Code extension |
| codex | `npm install -g @openai/codex` |
| gemini | `npm install -g @google/gemini-cli` (verify against research) |

---

## Per-CLI integration notes

### copilot

A working prototype exists at `specs/16-peer-review/copilot-staged-review.sh`. Key findings from the prototype:

- Invocation: `copilot -p "$PROMPT" -m MODEL --allow-tool='...' --deny-tool='write'`
- Output: JSON with schema `{ summary, overall_risk, findings: [{ severity, file, title, details, suggested_fix }] }`
- Severity values: `high | medium | low`
- The prototype passes `--allow-tool='shell(git diff --cached)'` so copilot fetches the diff itself. For Phase II, we embed the content directly in the prompt instead — this works for all target types (branch, PR, path) and avoids tool-permission complexity.
- `--deny-tool='write'` prevents file modifications.
- Parse `findings[]` from the JSON response; map `details` → problem, `suggested_fix` → fix.
- If `findings` array is empty, treat as `NO FINDINGS`.
- If JSON is malformed, fall through to raw-output fallback.

### codex

Needs research (see tasks Phase 1). Expected interface based on OpenAI CLI conventions:

- Binary: `codex`
- Prompt flag: likely `-p` or `--prompt`; may accept stdin
- Output format: likely markdown or plain text (not JSON)
- Read-only flag: likely `--no-auto-edit` or similar; verify
- Sub-model flag: likely `--model`

### gemini

Needs research (see tasks Phase 1). Expected interface based on Google Gemini CLI:

- Binary: `gemini`
- Prompt flag: likely `-p` or `--prompt`; may accept stdin
- Output format: likely markdown
- Read-only flag: TBD
- Sub-model flag: likely `--model`

---

## SKILL.md changes

Step 4 gains a conditional branch. Current Step 4 text (spawning Claude subagent) becomes the `else` branch. New structure:

```
### 4. Spawn Reviewer

If `model` starts with `claude-` (including the default `claude-opus-4-6`):
  [existing Claude subagent logic — unchanged]

Otherwise (external CLI path):
  [new 4a–4e logic above]
```

The output of both paths feeds into Step 5 unchanged.

---

## Evals strategy

External CLIs may not be installed in eval environments. Use **fixture-based evals**: the eval prompt tells the agent to simulate CLI output using a pre-defined fixture response (embedded in the eval's `prompt` field), then verify the skill correctly parses and presents it.

Three new evals:

- `copilot-json-parse`: agent receives a fixture copilot JSON response (embedded in the eval prompt) and must parse it into the standard findings format with correct severity normalization (`high` → `critical`, `medium` → `major`, `low` → `minor`)
- `codex-not-found`: agent runs `--model codex` when `codex` binary is absent; must error with install hint, not crash
- `gemini-no-findings`: agent receives a fixture gemini response indicating no findings; assertions: (1) the `## Peer Review —` header line is present; (2) "No issues found." follows on the next line; (3) no apply prompt is shown

Existing evals 1–3 remain unchanged (they use the default Claude path).

---

## Verification

After implementation:

1. `--model claude-opus-4-6` (default) → behaves identically to Phase I
2. `--model copilot` with copilot installed → routes to copilot CLI, parses JSON, presents normalized findings
3. `--model copilot:gpt-4o-mini` → passes `-m gpt-4o-mini` to copilot
4. `--model codex` when binary absent → error with install hint
5. `--model gemini` when binary absent → error with install hint
6. `npx cspell skills/peer-review/SKILL.md` → clean
7. `uv run --with pytest pytest tests/` → passes
