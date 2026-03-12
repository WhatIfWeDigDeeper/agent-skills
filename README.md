# agent-skills

Reusable skill definitions for Claude Code and other AI coding assistants. Skills are automated workflows that agents or users can invoke to perform specific tasks. See the [Agent Skills Standard](https://agentskills.io/).

## Available Skills

| Skill&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; | Description | Triggers | Eval&nbsp;Δ* |
|-------------|-------------|----------|--------|
| [js-deps](skills/js-deps/SKILL.md) | Security audits and dependency updates (npm, yarn, pnpm, bun) | "audit dependencies", "update packages", "fix vulnerabilities", "/js-deps", "/js-deps typescript", "/js-deps help" | [+62%](evals/js-deps/benchmark.json) |
| [learn](skills/learn/SKILL.md) | Extract lessons from conversations and persist to AI assistant configs (Claude, Cursor, Copilot, Gemini, etc.) and skills | "learn from this", "save this pattern", "/learn", "/learn help" | [+7%](evals/learn/benchmark.json) |
| [pr-comments](skills/pr-comments/SKILL.md) | Address review comments on your own PR: implement valid suggestions, reply to invalid ones, resolve threads, and credit commenters in commits | "address PR comments", "implement PR feedback", "respond to review comments", "/pr-comments", "/pr-comments 42" | [+82%](evals/pr-comments/benchmark.json) |
| [ship-it](skills/ship-it/SKILL.md) | Create branch, commit, push, and open a pull request | "ship it", "/ship-it" "/ship-it fix login timeout", "/ship-it help" | [+38%](evals/ship-it/benchmark.json) |
| [uv-deps](skills/uv-deps/SKILL.md) | Security audits and dependency updates for Python projects using uv | "audit Python packages", "update pyproject.toml", "fix Python CVEs", "/uv-deps", "/uv-deps fastapi", "/uv-deps help" | [+83%](evals/uv-deps/benchmark.json) |

\* pass-rate improvement with skill vs. without (see [evals/](evals/))

All skills support `help`, `--help`, `-h`, or `?` as arguments to show interactive options before running.

## Installation

### Using the skills package

Vercel's [skills package](https://github.com/vercel-labs/skills?tab=readme-ov-file#skills) is supported by almost all coding assistants. The skills in this repo are available on the skills.sh site at [skills.sh/whatifwedigdeeper/agent-skills](https://skills.sh/whatifwedigdeeper/agent-skills)

```bash
# prompts for which skills to install
npx skills add whatifwedigdeeper/agent-skills
```

```bash
# install an individual skill
npx skills add -y whatifwedigdeeper/agent-skills --skill pr-comments
```

### Manual installation by copying skill files

Pull down the repo. You may of course fork the repo first.

```bash
git clone https://github.com/WhatIfWeDigDeeper/agent-skills.git
cd agent-skills
```

Copy skill directories to your Claude or other assistant's skills folder.

```bash
# Project-level  (committed to version control)
# single skill
cp -r skills/learn {path to your directory}/.claude/skills/

# Copy all skills at once
cp -r skills/* {path to your directory}/.claude/skills/
```

```bash
# User-level (available in all projects)
cp -r skills/* ~/.claude/skills/
```

## Skill Notes

### `learn`

- Use `/learn help` to choose where learnings go (auto-route, skills only, or config only) and whether to write to all detected assistant configs at once.
- You can tell Coding Agent to focus on a particular problem if you like. If it is a long conversation, it may result in "context rot" so it is more likely that it may miss a problem you want to avoid in the future.

  ```text
  /learn tests were not run
  ```

### `ship-it`

- Use `/ship-it help` to choose workflow scope (full PR, commit only, or push only) and PR options (draft, self-merge).
- **Selective staging**: The skill reviews changed files and stages them individually, excluding secrets and build artifacts.
- **Pre-push validation** is left to your git hooks (pre-commit, pre-push). The skill does not run build/lint/test itself — configure hooks to enforce those checks.
- **Default branch detection** is automatic via local remote refs. Works with `main`, `master`, or any custom default.
- **Co-authorship**: By default, agents append their own co-author trailer per their conventions. To skip this, include "no co-author" in your arguments (e.g., `/ship-it fix login, no co-author`).

### `js-deps`

- Use `/js-deps help` to choose between updating dependencies or fixing security vulnerabilities, then pick version filters (major/minor/patch, skip .0 patches) or vulnerability severity levels (critical/high/moderate/all) to fix.
- Without passing in "help", you can tell your AI Coding Agent to skip zero patch releases `{major}.{minor}.0` until it becomes more stable.

  ```text
  /js-deps skip 0 patch versions except for @types/* files
  ```

- You can also pass in specific packages

  ```text
  /js-deps typescript
  ```

### `uv-deps`

- Use `/uv-deps help` to choose between updating dependencies or fixing security vulnerabilities, then pick version filters or vulnerability severity levels.
- Targets `pyproject.toml`-based projects managed by `uv`. Projects using only `requirements.txt`, `setup.py`, poetry, or pipenv are out of scope.
- Pass specific package names, `.` for all packages, or glob patterns:

  ```text
  /uv-deps fastapi asyncpg
  /uv-deps django-*
  /uv-deps .
  ```

- Requires `uv` and `uvx` to be installed and accessible. All git and `gh` commands run with sandbox disabled for keyring access.


### `pr-comments`

- Pass a PR number to target a specific PR (e.g., `/pr-comments 42`), or omit it to detect from the current branch.
- The skill presents a plan for your approval before making any changes — you can override its judgment on which comments to implement vs. decline.
- Implemented comments are committed with `Co-authored-by` trailers crediting each reviewer.
- Resolved threads are closed via the GitHub GraphQL API; declined threads remain open so reviewers can follow up.
- Requires `gh` CLI with repo access. Runs with sandbox disabled for keyring access.

## Updating Skills

Usually you'd run the following, but as of 2026-02-13 this doesn't appear to pick up changes for me.

```bash
npx skills check
# or update
npx skills update
```

You can force installing the latest skill with `-y`.

```bash
npx skills add -y whatifwedigdeeper/agent-skills --skill ship-it
```

Alternatively you can remove and then re-add the skills(s)

```bash
npx skills rm whatifwedigdeeper/agent-skills --skill ship-it
npx skills add whatifwedigdeeper/agent-skills --skill ship-it
```

## Contributing

You are more than welcome to submit PRs to update existing skills. If you are interested in adding new skills, you may want to consider adding them to more popular skill distribution repos. I may submit some of these skills as PRs to more popular skill distribution repos, if similar skills do not already exist. However, that requires more substantial testing and usage to refine the skills. If you do install and use these skills, opening an issue or PR would be very helpful in that process. Thanks!

### Local Setup

After cloning, create symlinks so Claude Code can discover the skills from this repo directly:

```bash
for d in skills/*/; do ln -sf "../../$d" ".claude/skills/$(basename $d)"; done
```

This links each `skills/<name>/` into `.claude/skills/<name>` using relative paths. The `.claude/skills/` directory is gitignored, so this is a one-time local setup step.

There are regression tests you can run for the skills.

```bash
uv run --with pytest pytest tests/ -v
```

You may also use Anthropic's [skill-creator](https://github.com/anthropics/skills/blob/main/skills/skill-creator/SKILL.md) to review the existing skill.

```bash
# if you haven't already installed it
npx skills add -y anthropics/skills/ --skill skill-creator
```

Ask to review a particular skill or skills

```text
/skill-creator review ship-it
```
