# CLI Research: gemini

**Status**: Not available in this environment — skipping gemini integration phase.

## Verification

```
$ which gemini
gemini not found
```

## Planned Interface (from Google Gemini CLI conventions)

- Binary: `gemini`
- Prompt flag: likely `-p` or `--prompt`; may accept stdin
- Output format: likely markdown
- Read-only flag: TBD from research
- Sub-model flag: likely `--model`

## Install Command

```bash
npm install -g @google/gemini-cli
```

Note: verify package name against official Google documentation before publishing.

## Fallback in SKILL.md

When gemini binary is absent, the skill outputs:

```
gemini CLI not found. Install with: npm install -g @google/gemini-cli
```

and exits without attempting a review.
