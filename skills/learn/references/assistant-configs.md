# Assistant Configuration Reference

## Format Compatibility

| Format | Assistants | Notes |
|--------|-----------|-------|
| Markdown | Claude, Gemini, AGENTS.md, Copilot, Windsurf, Cursor (legacy) | Most universal |
| MDC | Cursor (modern) | Markdown with YAML frontmatter |
| JSON | Continue | Requires `customInstructions` key |

## Markdown Config Structure

For markdown-based configs (CLAUDE.md, GEMINI.md, AGENTS.md, Copilot, Windsurf), use standard markdown sections. Find the most relevant existing section and append; create a new section only when no existing section fits.

## Non-Markdown Formats

When writing to Cursor or Continue configs, **MANDATORY: read the format reference before writing**:

- **Cursor MDC** (`.cursor/rules/*.mdc`): read [`format-cursor-mdc.md`](format-cursor-mdc.md) in full — MDC uses YAML frontmatter with `description`, `globs`, and `alwaysApply` fields. Do NOT treat `.mdc` files like plain markdown.
- **Continue** (`.continuerc.json`): read [`format-continue.md`](format-continue.md) in full — learnings go in the `customInstructions` JSON string field. Do NOT create a markdown file.
- **Legacy Cursor** (`.cursorrules`): plain markdown, no special format needed.

Do NOT load these format references when writing to markdown-based configs (CLAUDE.md, GEMINI.md, AGENTS.md, Copilot, Windsurf).

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
