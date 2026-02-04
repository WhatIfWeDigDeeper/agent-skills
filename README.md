# agent-skills

Reusable skill definitions for Claude Code and other AI coding assistants. Skills are automated workflows that agents or users can invoke to perform specific tasks. See the [Agent Skills Standard](https://agentskills.io/).

## Available Skills

| Skill | Description | Triggers |
|-------|-------------|----------|
| [learn](skills/learn/SKILL.md) | Extract lessons from conversations and persist to CLAUDE.md | "learn from this", "save this pattern" |
| [package-json-maintenance](skills/package-json-maintenance/SKILL.md) | Security audits and dependency updates (npm, yarn, pnpm, bun) | "audit dependencies", "update packages", "check for vulnerabilities" |

## Installation

### Using npx, supported by most coding assistants

```bash
npx skills add whatifwedigdeeper/agent-skills \
--skill learn
```

```bash
npx skills add whatifwedigdeeper/agent-skills \
--skill package-json-maintenance
```

### Using the Claude specific plugin marketplace

```bash
/plugin marketplace add whatifwedigdeeper/agent-skills
```

And then install the skill you want

```bash
/plugin install package-json-maintenance
```

```bash
/plugin install learn
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

## Usage

After installation, skills are triggered naturally in conversation:

- "What are the lessons learned?"
- "Run a security audit on my dependencies"
- "Update my npm packages to latest versions"
- "Fix vulnerabilities"

Or you can explicitly invoke them.

```bash
/learn
```

```bash
/package-json-maintenance
```

You can also provide arguments to narrow the scope.

```bash
# for a specific directory in a monorepo
/package-json-maintenance api/
# only update specific packages
/package-json-maintenance jest @types/jest
```

## Contributing

You may submit PRs to update existing skills. I would advise against adding submitting new skills as ultimately I will probably submit these skills as PRs to more popular skill distribution repos, assuming similar skills do not exist. That requires more substantial testing and use to refine the skills. If you do install and use these skills, opening an issue or PR would be very helpful in that process. Thanks!
