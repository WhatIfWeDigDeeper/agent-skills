# Assistant Configuration Reference

## Config File Locations

| Assistant | Primary Location | Format |
|-----------|-----------------|--------|
| Claude Code | `CLAUDE.md` | Markdown |
| Gemini | `GEMINI.md` | Markdown |
| AGENTS.md | `AGENTS.md` | Markdown |
| Cursor (legacy) | `.cursorrules` | Markdown |
| Cursor (modern) | `.cursor/rules/*.mdc` | MDC (Markdown + frontmatter) |
| GitHub Copilot | `.github/copilot-instructions.md` | Markdown |
| Windsurf | `.windsurf/rules/rules.md` | Markdown |
| Continue | `.continuerc.json` | JSON |

## Detection Commands

```bash
# Check each config file
[ -f "CLAUDE.md" ] && echo "claude"
[ -f "GEMINI.md" ] && echo "gemini"
[ -f "AGENTS.md" ] && echo "agents"
[ -f ".cursorrules" ] && echo "cursor-legacy"
[ -d ".cursor/rules" ] && echo "cursor"
[ -f ".github/copilot-instructions.md" ] && echo "copilot"
[ -f ".windsurf/rules/rules.md" ] && echo "windsurf"
[ -f ".continuerc.json" ] && echo "continue"
```

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
