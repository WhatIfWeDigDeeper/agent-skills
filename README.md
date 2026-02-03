# agent-skills

Reusable skill definitions for Claude Code and other coding assistants. Skills are automated workflows that agents can invoke to perform specific tasks like security audits, dependency updates, and learning from conversations.

## Available Skills

| Skill | Description |
|-------|-------------|
| [learn](skills/learn/SKILL.md) | Analyzes conversations to extract lessons learned and persist them to CLAUDE.md or skills |
| [npm-audit-and-fix](skills/npm-audit-and-fix/SKILL.md) | Security audit with automatic fixes for vulnerabilities |
| [npm-update-dependencies](skills/npm-update-dependencies/SKILL.md) | Update npm packages to latest versions with validation |

## Installation

### Using Claude Code's /plugin command

```
/plugin add https://github.com/whatifwedigdeeper/agent-skills
```

### Using npx

```sh
npx skills add https://github.com/whatifwedigdeeper/agent-skills --skill learn
```
