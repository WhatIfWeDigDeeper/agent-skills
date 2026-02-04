---
name: learn
description: Analyzes conversations to extract lessons learned (corrections, discoveries, workarounds) and persists them to CLAUDE.md and/or updates existing skills or creates new skills. Use after completing tasks that involved retries, debugging, finding workarounds, or discovering undocumented behavior.
license: MIT
metadata:
  author: Gregory Murray
  repository: github.com/whatifwedigdeeper/agent-skills
  version: "0.1"
---

# Learn from Conversation

Analyze the conversation to extract lessons learned, then persist them to project configuration.

## Process

### 1. Analyze Conversation

Scan for:
- **Corrections**: Commands retried, assumptions proven wrong, missing prerequisites
- **Discoveries**: Undocumented patterns, integration quirks, environment requirements
- **Improvements**: Steps that should be automated or validated earlier

### 2. Categorize Each Learning

| Category | Destination | Examples |
|----------|-------------|----------|
| Project facts | CLAUDE.md | Conventions, patterns, architecture decisions |
| Prerequisites | CLAUDE.md | Required state before running commands |
| Environment | CLAUDE.md | Required env vars, services, configuration |
| Automated workflow | New skill | Multi-step processes to suggest proactively |

### 3. Present and Confirm

For each learning, show:
```
**[Category]**: [Brief description]
- Source: [What happened in conversation]
- Proposed change: [Exact text or file to add]
```

Ask for confirmation before applying each change.

### 4. Apply Changes

**CLAUDE.md updates**: Find appropriate section, preserve existing structure.

**New skills**: Create in `skills/[name]/SKILL.md`, follow existing patterns.

### 5. Summarize

List files modified and sections updated.

## Examples

| Situation | Learning |
|-----------|----------|
| "e2e tests failed because API wasn't running" | Add prerequisite to CLAUDE.md |
| "Parse SDK doesn't work with Vite out of the box" | Document workaround in CLAUDE.md |
| "Build failed because NODE_ENV wasn't set" | Add required env var to CLAUDE.md |
| "Every component needs tests, lint, build..." | Create `add-component` skill |

## Guidelines

- **Be specific**: Include exact commands, paths, error messages
- **Be minimal**: Only add what genuinely helps future sessions
- **Avoid duplication**: Check for existing similar content first
- **Preserve structure**: Fit into existing CLAUDE.md organization
