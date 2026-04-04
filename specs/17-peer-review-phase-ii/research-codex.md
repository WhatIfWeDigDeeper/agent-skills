# CLI Research: codex

**Status**: Not available in this environment — skipping codex integration phase.

## Verification

```
$ which codex
codex not found
```

## Planned Interface (from OpenAI CLI conventions)

- Binary: `codex`
- Prompt flag: likely `-p` or `--prompt`; may accept stdin
- Output format: likely markdown or plain text (not JSON)
- Read-only flag: likely `--no-auto-edit` or similar
- Sub-model flag: likely `--model`

## Install Command

```bash
npm install -g @openai/codex
```

## Fallback in SKILL.md

When codex binary is absent, the skill outputs:

```
codex CLI not found. Install with: npm install -g @openai/codex
```

and exits without attempting a review.
