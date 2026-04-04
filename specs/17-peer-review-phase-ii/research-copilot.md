# CLI Research: copilot

**Status**: Available — proceeding with integration.

**Binary path**: On this machine, `which copilot` resolved to the installed copilot binary.

## Flags

| Flag | Description |
|------|-------------|
| `-p, --prompt <text>` | Execute a prompt in non-interactive mode |
| `-m, --model <model>` | Set the AI model to use |
| `--allow-all-tools` | Allow all tools to run automatically without confirmation; **required for non-interactive (`-p`) mode** |
| `--deny-tool[=tools...]` | Tools the CLI does not have permission to use; overrides `--allow-all-tools` |
| `--allow-tool[=tools...]` | Tools the CLI has permission to use without prompting |

## Output Format (from prototype)

JSON with schema:
```json
{
  "summary": "...",
  "overall_risk": "low | medium | high",
  "findings": [
    {
      "severity": "high | medium | low",
      "file": "relative/path",
      "title": "One-line summary",
      "details": "Problem description",
      "suggested_fix": "Fix description"
    }
  ]
}
```

- `details` maps to the `problem` field in peer-review's normalized findings
- `suggested_fix` maps to the `fix` field
- Severity values `high`, `medium`, `low` are normalized to `critical`, `major`, `minor`
- Empty `findings` array → treat as `NO FINDINGS`
- Malformed JSON → raw-output fallback

## Invocation (confirmed)

For Phase II, embed diff/PR content directly in the prompt (no `--allow-tool='shell(git diff ...)'` needed):

```bash
REVIEW_OUTPUT=$(copilot --allow-all-tools --deny-tool=write -p "$(cat "$PROMPT_FILE")" [-m SUBMODEL])
```

`--allow-all-tools` is required for non-interactive (`-p`) mode. `--deny-tool=write` prevents file modifications.

## Notes

- The earlier prototype (`specs/16-peer-review/copilot-staged-review.sh`) used `--allow-tool='shell(git diff --cached)'` to let copilot fetch the diff itself. Phase II embeds content in the prompt instead, which works for all target types.
- The `--deny-tool='write'` syntax from the prototype may require the quoted form; `--deny-tool=write` (no quotes) also works per help output.
