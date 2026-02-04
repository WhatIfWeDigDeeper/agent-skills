---
name: learn
description: Analyzes conversations to extract lessons learned (corrections, discoveries, workarounds) and persists them to AI assistant configuration files. Supports CLAUDE.md, GEMINI.md, AGENTS.md, Cursor rules, GitHub Copilot instructions, Windsurf rules, and Continue config. Use after completing tasks that involved retries, debugging, finding workarounds, or discovering undocumented behavior.
arguments: Optional - specific assistant names to target (e.g., "claude cursor")
license: MIT
metadata:
  author: Gregory Murray
  repository: github.com/whatifwedigdeeper/agent-skills
  version: "0.2"
---

# Learn from Conversation

Analyze the conversation to extract lessons learned, then persist them to AI assistant configuration files.

## Supported Assistants

| Assistant | Config File | Format |
|-----------|-------------|--------|
| Claude Code | `CLAUDE.md` | Markdown |
| Gemini | `GEMINI.md` | Markdown |
| AGENTS.md | `AGENTS.md` | Markdown |
| Cursor | `.cursorrules` or `.cursor/rules/*.mdc` | Markdown/MDC |
| GitHub Copilot | `.github/copilot-instructions.md` | Markdown |
| Windsurf | `.windsurf/rules/rules.md` | Markdown |
| Continue | `.continuerc.json` | JSON |

See [references/assistant-configs.md](references/assistant-configs.md) for format details.

## Process

### 1. Detect Assistant Configurations

Scan for existing config files:

```bash
[ -f "CLAUDE.md" ] && echo "claude"
[ -f "GEMINI.md" ] && echo "gemini"
[ -f "AGENTS.md" ] && echo "agents"
[ -f ".cursorrules" ] && echo "cursor-legacy"
[ -d ".cursor/rules" ] && echo "cursor"
[ -f ".github/copilot-instructions.md" ] && echo "copilot"
[ -f ".windsurf/rules/rules.md" ] && echo "windsurf"
[ -f ".continuerc.json" ] && echo "continue"
```

**Behavior based on detection:**

| Scenario | Action |
|----------|--------|
| Single config found | Update it automatically |
| Multiple configs found | Prompt user to select which to update |
| No configs found | Guide user to initialize one first, then exit |

**When no configs found**, display:
```
No AI assistant configuration files detected.

Please initialize one first using your assistant's setup command:
- Claude Code: claude /init
- Cursor: Create .cursorrules or use Settings
- Copilot: Create .github/copilot-instructions.md
- Gemini: Create GEMINI.md
- Universal: Create AGENTS.md

Then run /learn again.
```

### 2. Analyze Conversation

Scan for:
- **Corrections**: Commands retried, assumptions proven wrong, missing prerequisites
- **Discoveries**: Undocumented patterns, integration quirks, environment requirements
- **Improvements**: Steps that should be automated or validated earlier

### 3. Categorize Each Learning

| Category | Destination | Examples |
|----------|-------------|----------|
| Project facts | Selected config(s) | Conventions, patterns, architecture decisions |
| Prerequisites | Selected config(s) | Required state before running commands |
| Environment | Selected config(s) | Required env vars, services, configuration |
| Automated workflow | New skill | Multi-step processes to suggest proactively |

### 4. Present and Confirm

For each learning, show:
```
**[Category]**: [Brief description]
- Source: [What happened in conversation]
- Proposed change: [Exact text or file to add]
- Destination(s): [List of config files to update]
```

Ask for confirmation before applying each change.

### 5. Apply Changes

Apply changes based on config file format:

**Markdown configs** (CLAUDE.md, GEMINI.md, AGENTS.md, Copilot, Windsurf):
- Find appropriate section, preserve existing structure
- Append to relevant section or create new section if needed

**Cursor rules**:
- Legacy `.cursorrules`: Treat like markdown, append content
- Modern `.cursor/rules/*.mdc`: See [references/format-cursor-mdc.md](references/format-cursor-mdc.md)

**Continue** (`.continuerc.json`):
- Update `customInstructions` field, preserving existing content
- See [references/format-continue.md](references/format-continue.md)

**New skills**: Create in `skills/[name]/SKILL.md`, follow existing patterns.

### 6. Summarize

List:
- Config files modified (with full paths)
- Sections updated in each file
- Any skills created

## Examples

| Situation | Learning |
|-----------|----------|
| "e2e tests failed because API wasn't running" | Add prerequisite to selected config(s) |
| "Parse SDK doesn't work with Vite out of the box" | Document workaround in selected config(s) |
| "Build failed because NODE_ENV wasn't set" | Add required env var to selected config(s) |
| "Every component needs tests, lint, build..." | Create `add-component` skill |

## Edge Cases

| Scenario | Handling |
|----------|----------|
| No configs detected | Guide user to initialize one first, exit early |
| Multiple configs found | Prompt user to select which to update |
| Malformed config file | Warn and skip that file |
| Duplicate content exists | Check before adding, warn if similar learning exists |

## Guidelines

- **Be specific**: Include exact commands, paths, error messages
- **Be minimal**: Only add what genuinely helps future sessions
- **Avoid duplication**: Check for existing similar content in all selected configs
- **Preserve structure**: Fit into existing config file organization
- **Respect format**: Adapt content appropriately for each assistant's format
