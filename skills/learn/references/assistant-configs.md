# Assistant Configuration Reference

## Format Compatibility

| Format | Assistants | Notes |
|--------|-----------|-------|
| Markdown | Claude, Gemini, AGENTS.md, Copilot, Windsurf, Cursor (legacy) | Most universal |
| MDC | Cursor (modern) | Markdown with YAML frontmatter |
| JSON | Continue | Requires `customInstructions` key |

## Markdown Config Structure

For markdown-based configs (CLAUDE.md, GEMINI.md, AGENTS.md, Copilot, Windsurf), use standard markdown sections:

```markdown
# Project Instructions

## Conventions
- Convention 1
- Convention 2

## Prerequisites
- Required setup step

## Environment
- Required env vars
```

## Initialization Commands

When no config exists, guide users to their assistant's init process:

| Assistant | How to Initialize |
|-----------|------------------|
| Claude Code | `claude /init` |
| Cursor | Create `.cursorrules` or use Settings > Rules |
| GitHub Copilot | Create `.github/copilot-instructions.md` manually |
| Windsurf | Create `.windsurf/rules/rules.md` manually |
| Continue | Create `.continuerc.json` with `{"customInstructions": ""}` |
| Gemini | Create `GEMINI.md` manually |
| Universal | Create `AGENTS.md` manually |
