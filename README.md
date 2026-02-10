# agent-skills

Reusable skill definitions for Claude Code and other AI coding assistants. Skills are automated workflows that agents or users can invoke to perform specific tasks. See the [Agent Skills Standard](https://agentskills.io/).

## Available Skills

| Skill | Description | Triggers |
|-------|-------------|----------|
| [learn](skills/learn/SKILL.md) | Extract lessons from conversations and persist to AI assistant configs (Claude, Cursor, Copilot, Gemini, etc.) and skills | "learn from this", "save this pattern", "/learn" |
| [package-json-maintenance](skills/package-json-maintenance/SKILL.md) | Security audits and dependency updates (npm, yarn, pnpm, bun) | "audit dependencies", "update packages", "fix vulnerabilities", "/package-json-maintenance typescript" |
| [ship-it](skills/ship-it/SKILL.md) | Create branch, commit, push, and open a pull request | "ship it", "ship this", "/ship-it", "/ship-it fix login timeout" |

## Installation

### Using the [skills package](https://github.com/vercel-labs/skills?tab=readme-ov-file#skills), supported by most coding assistants

```bash
# prompts for which skills to install
npx skills add whatifwedigdeeper/agent-skills
```

### Manual installation by copying skill files

Pull down the repo. You may of course fork the repo first.

```bash
git clone https://github.com/WhatIfWeDigDeeper/agent-skills.git
```

Copy skill directories to your Claude or other assistant's skills folder:

```bash
# Project-level (committed to version control)
cp -r skills/package-json-maintenance {path to your directory}/.claude/skills/
```

```bash
# User-level (available in all projects)
cp -r skills/learn ~/.claude/skills/
```

## Skill Notes

### ship-it

- **Stages all changes** (`git add -A`). If you need selective staging, stage files manually before invoking the skill.
- **Pre-push validation** is left to your git hooks (pre-commit, pre-push). The skill does not run build/lint/test itself — configure hooks to enforce those checks.
- **Default branch detection** is automatic via `git remote show origin`. Works with `main`, `master`, or any custom default.
- **Co-authorship attribution** is agent-dependent. Each agent appends its own co-author trailer (or not) per its conventions.

## Contributing

You are more than welcome to submit PRs to update existing skills. There are regression tests you can run for the skills.

```bash
uv run --with pytest pytest tests/ -v
```

I would advise against adding new skills as I will most likely submit these skills as PRs to more popular skill distribution repos, if similar skills do not exist. That requires more substantial testing and usage to refine the skills. If you do install and use these skills, opening an issue or PR would be very helpful in that process. Thanks!
