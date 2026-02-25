# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a collection of reusable skill definitions for Claude Code and other coding assistants. Skills are automated workflows defined in SKILL.md files that agents can invoke to perform specific tasks.

## Repository Structure

```
skills/
  <skill-name>/
    SKILL.md     # Skill definition with frontmatter + workflow
```

## Skill Definition Format

Each skill follows this structure:

```markdown
---
name: skill-name
description: Brief description of what the skill does
license: MIT (optional)
compatibility: Runtime or access requirements (optional)
metadata: (optional)
  author: Author Name
  repository: github.com/org/repo
  version: "1.0"
---

# Skill Title

Workflow documentation with:
- Process sections numbered (### 1. Step Name)
- Bash code blocks for executable commands
- Tables for categorization/options
- Example outputs
```

Valid frontmatter fields: `name`, `description` (required), `license`, `compatibility`, `metadata` (optional). The skill-creator skill may suggest limiting to `name` and `description`, but all fields shown above are part of the skills spec and should not be flagged as violations.

## Adding New Skills

1. Create directory: `skills/<skill-name>/`
2. Create `SKILL.md` following the format above
3. Include YAML frontmatter with name and description
4. Document the workflow with numbered process steps
5. Add bash code blocks for commands that should be executed
6. Include example outputs where helpful

## Sandbox Workarounds

- **GPG signing**: `git commit` may fail if GPG keyring is inaccessible. Use `--no-gpg-sign` as a fallback.
- **Heredocs**: `$(cat <<'EOF'...)` may fail with "can't create temp file". Use multiple `-m` flags for commit messages or write content to a temp file first.

## Spell Checking

This repo uses cspell. When a technical term triggers a false-positive spelling warning (e.g. `pyproject`, `uvx`, `subagent`), add it to the `words` list in `cspell.config.yaml` rather than ignoring or suppressing the warning.

## Git Workflow

- After merging a PR, delete the local and remote feature branch and switch to main with a pull.

## Skill Design Patterns

- **Isolation**: Use dedicated branches to test changes without affecting the main working directory
- **Validation**: Run build/lint/test after making changes
- **Parallelization**: Use Task subagents for processing multiple items concurrently
- **Documentation sync**: Update CLAUDE.md/README.md when major versions change
- **PR-driven**: Create pull requests for review rather than auto-committing
