# agent-skills

Reusable skill definitions for Claude Code and other AI coding assistants. Skills are automated workflows that agents or users can invoke to perform specific tasks. See the [Agent Skills Standard](https://agentskills.io/).

## Available Skills

| Skill | Description | Triggers |
|-------|-------------|----------|
| [learn](skills/learn/SKILL.md) | Extract lessons from conversations and persist to AI assistant configs (Claude, Cursor, Copilot, Gemini, etc.) and skills | "learn from this", "save this pattern", "/learn" |
| [package-json-maintenance](skills/package-json-maintenance/SKILL.md) | Security audits and dependency updates (npm, yarn, pnpm, bun) | "audit dependencies", "update packages", "fix vulnerabilities", "/package-json-maintenance typescript" |

## Installation

### Using the [skills package](https://github.com/vercel-labs/skills?tab=readme-ov-file#skills), supported by most coding assistants

```bash
npx skills add whatifwedigdeeper/agent-skills \
--skill learn
```

```bash
npx skills add whatifwedigdeeper/agent-skills \
--skill package-json-maintenance
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

## Contributing

You are more than welcome to submit PRs to update existing skills. There are regression tests you can run for the skills.

```bash
uv run --with pytest pytest tests/ -v
```

I would advise against adding new skills as I will most likely submit these skills as PRs to more popular skill distribution repos, if similar skills do not exist. That requires more substantial testing and usage to refine the skills. If you do install and use these skills, opening an issue or PR would be very helpful in that process. Thanks!
