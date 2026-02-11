# agent-skills

Reusable skill definitions for Claude Code and other AI coding assistants. Skills are automated workflows that agents or users can invoke to perform specific tasks. See the [Agent Skills Standard](https://agentskills.io/).

## Available Skills

| Skill | Description | Triggers |
|-------|-------------|----------|
| [learn](skills/learn/SKILL.md) | Extract lessons from conversations and persist to AI assistant configs (Claude, Cursor, Copilot, Gemini, etc.) and skills | "learn from this", "save this pattern", "/learn" |
| [js-deps](skills/js-deps/SKILL.md) | Security audits and dependency updates (npm, yarn, pnpm, bun) | "audit dependencies", "update packages", "fix vulnerabilities", "/js-deps typescript" |
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

<details>
<summary>Clone and Manually Copy</summary>

Clone repo

```bash
git clone https://github.com/WhatIfWeDigDeeper/agent-skills.git
cd agent-skills
```

Copy skill directories to your Claude or other assistant's skills folder.

```bash
# Project-level  (committed to version control)
# single skill
cp -r skills/js-deps {path to your directory}/.claude/skills/

# Copy all skills at once
cp -r skills/* {path to your directory}/.claude/skills/
```

```bash
# User-level (available in all projects)
cp -r skills/* ~/.claude/skills/
```

</details>

## Skill Notes

### ship-it

- **Selective staging**: The skill reviews changed files and stages them individually, excluding secrets and build artifacts.
- **Pre-push validation** is left to your git hooks (pre-commit, pre-push). The skill does not run build/lint/test itself — configure hooks to enforce those checks.
- **Default branch detection** is automatic via local remote refs. Works with `main`, `master`, or any custom default.
- **Co-authorship**: By default, agents append their own co-author trailer per their conventions. To skip this, include "no co-author" in your arguments (e.g., `/ship-it fix login, no co-author`).

## Contributing

You are more than welcome to submit PRs to update existing skills. There are regression tests you can run for the skills.

```bash
uv run --with pytest pytest tests/ -v
```

You may also use Anthropic's [skill-creator](https://github.com/anthropics/skills/blob/main/skills/skill-creator/SKILL.md) to review the existing skill

```text
/skill-creator review ship-it
```

If you are interested in adding new skills, you may want to consider adding them to more popular skill distribution repos.
I may submit some of these skills as PRs to more popular skill distribution repos, if similar skills do not already exist. However, that requires more substantial testing and usage to refine the skills. If you do install and use these skills, opening an issue or PR would be very helpful in that process. Thanks!
