# agent-skills

Reusable skill definitions for Claude Code and other AI coding assistants. Skills are automated workflows that agents or users can invoke to perform specific tasks. See the [Agent Skills Standard](https://agentskills.io/).

## Available Skills

| Skill&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; | Description | Triggers | Eval&nbsp;Δ* |
|-------------|-------------|----------|--------|
| [js-deps](skills/js-deps/SKILL.md) | Security audits and dependency updates (npm, yarn, pnpm, bun) | "audit dependencies", "update packages", "fix vulnerabilities", "/js-deps", "/js-deps typescript", "/js-deps help" | [+38%](evals/js-deps/benchmark.md) |
| [learn](skills/learn/SKILL.md) | Extract lessons from conversations and persist to AI assistant configs (Claude, Cursor, Copilot, Gemini, etc.) and skills | "learn from this", "save this pattern", "/learn", "/learn help" | [+10% Sonnet 4.6 / +0% Opus 4.7](evals/learn/benchmark.md) |
| [peer-review](skills/peer-review/SKILL.md) | Fresh-context review of staged changes, branches, PRs, or file sets — returns severity-grouped findings you can apply or skip | "peer review", "peer review PR 42", "peer review staged", "review with Gemini", "fresh review", "another set of eyes", "/peer-review", "/peer-review --staged", "/peer-review --pr 42", "/peer-review skills/pr-comments/" | [+26%](evals/peer-review/benchmark.md) |
| [pr-comments](skills/pr-comments/SKILL.md) | Address review comments on your own PR: implement valid suggestions, reply to invalid ones, resolve threads, credit commenters in commits, push and re-request review, and poll for bot reviewers across multiple rounds hands-free (auto mode by default; use `--manual` to confirm each iteration) | "address PR comments", "implement PR feedback", "respond to review comments", "/pr-comments", "/pr-comments 42", "/pr-comments --max 5", "/pr-comments --manual" | [+66%](evals/pr-comments/benchmark.md) |
| [pr-human-guide](skills/pr-human-guide/SKILL.md) | Analyzes a PR diff and appends a categorized review guide to the PR description, highlighting areas that need human judgment: security, config/infra, new dependencies, data model changes, novel patterns, and concurrency | "review guide", "human review guide", "prep for review", "flag for review", "/pr-human-guide", "/pr-human-guide 42" | [+39%](evals/pr-human-guide/benchmark.md) |
| [ship-it](skills/ship-it/SKILL.md) | Create branch, commit, push, and open a pull request | "ship it", "/ship-it" "/ship-it fix login timeout", "/ship-it help" | [+38%](evals/ship-it/benchmark.md) |
| [uv-deps](skills/uv-deps/SKILL.md) | Security audits and dependency updates for Python projects using uv | "audit Python packages", "update pyproject.toml", "fix Python CVEs", "/uv-deps", "/uv-deps fastapi", "/uv-deps help" | [+83%](evals/uv-deps/benchmark.md) |

\* pass-rate improvement with skill vs. without (see [evals/](evals/))

All skills support `help`, `--help`, `-h`, or `?` as arguments to show interactive options before running.

## Installation

### Using the skills package

Vercel's [skills package](https://github.com/vercel-labs/skills?tab=readme-ov-file#skills) is supported by almost all coding assistants. The skills in this repo are available on Vercel's skills site at [https://skills.sh/whatifwedigdeeper/agent-skills](https://skills.sh/whatifwedigdeeper/agent-skills)

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

### `peer-review`

- Use `/peer-review --staged` (or just `/peer-review`) to review staged changes before committing, `/peer-review --pr N` for an existing PR, `/peer-review --branch NAME` for a branch diff, or pass a path to check consistency across related files.
- Use `--focus TOPIC` to emphasize a specific area (e.g. `--focus security`, `--focus consistency`) — critical findings outside the focus are still reported.
- **vs `code-review`**: `code-review` spawns multiple reviewer personas and is best for thorough pre-merge PR reviews. `peer-review` is a single fresh-context reviewer optimized for lighter checks: quick consistency sweeps and staged-change review.
- **Multi-LLM routing**: pass `--model copilot[:submodel]`, `--model codex`, or `--model gemini` to route the review to an external CLI instead of the default Claude reviewer. The binary must be installed (`npm install -g @github/copilot-cli` / `@openai/codex` / `@google/gemini-cli`). Each CLI's output is normalized to the same severity-grouped findings format.
- **Triage layer**: when using an external CLI (`--model copilot/codex/gemini`), a Claude subagent automatically triages findings — classifying each as `recommend` or `skip` based on whether the issue is real, actionable, and not already addressed in the reviewed content. Skipped findings are shown transparently below the apply prompt with `S`-prefix numbering; users can override triage by including an S-number in their reply (e.g. `1,S2`).
- **Post-apply re-scan**: after applying findings, the skill offers to re-scan the modified files for new issues introduced by the edits. The re-scan always uses consistency mode and always uses Claude regardless of the original `--model`. Offered at most once per invocation.
- **Eval cost**: with-skill runs ~5.0 seconds faster and ~688 tokens heavier than baseline on average; time/token stats are from 7 measured evals (1, 3–4 and 11–14) — eval 2 measurements excluded as stale pre-v1.3 data; 13 evals use simulated transcripts and have no time/token measurements ([details](evals/peer-review/benchmark.md))

### `learn`

- Use `/learn help` to choose where learnings go (auto-route, skills only, or config only) and whether to write to all detected assistant configs at once.
- **Eval cost**: on Sonnet 4.6 +26.0 seconds and +3,258 tokens over baseline for +10% pass rate (4 evals, only eval 2 discriminating); on Opus 4.7 +4.3 seconds and +8,062 tokens for +0% — the stronger baseline already handles multi-target routing, plan-before-apply, and update-in-place on its own ([details](evals/learn/benchmark.md))
- You can tell Coding Agent to focus on a particular problem if you like. If it is a long conversation, it may result in "context rot" so it is more likely that it may miss a problem you want to avoid in the future.

  ```text
  /learn tests were not run
  ```

### `pr-human-guide`

- Run `/pr-human-guide` on the current branch's PR, or pass a PR number: `/pr-human-guide 42`.
- Produces a categorized **Review Guide** section appended to the PR description — organized by concern type (Security, Config/Infrastructure, New Dependencies, Data Model Changes, Novel Patterns, Concurrency/State). Categories with no flagged items are omitted.
- **Novel pattern detection** compares the diff against sibling files to identify code that doesn't match existing codebase conventions — new frameworks, different error handling strategies, first use of a library.
- **Idempotent**: re-running after new commits replaces the existing guide rather than appending a duplicate.
- **Complementary to other review skills**: `peer-review` does automated code review; `pr-human-guide` tells the human reviewer where to focus their own judgment.
- **Eval cost**: +20.9 seconds, +5,517 tokens over baseline ([details](evals/pr-human-guide/benchmark.md)); measured across 8 evals (cost of reading `SKILL.md` and `categories.md`), 6 of 8 of which discriminate (+39% delta).

### `ship-it`

- Use `/ship-it help` to choose workflow scope (full PR, commit only, or push only) and PR options (draft, self-merge).
- **Selective staging**: The skill reviews changed files and stages them individually, excluding secrets and build artifacts.
- **Pre-push validation** is left to your git hooks (pre-commit, pre-push). The skill does not run build/lint/test itself — configure hooks to enforce those checks.
- **Default branch detection** is automatic via local remote refs. Works with `main`, `master`, or any custom default.
- **Co-authorship**: By default, agents append their own co-author trailer per their conventions. To skip this, include "no co-author" in your arguments (e.g., `/ship-it fix login, no co-author`).
- **Eval cost**: +41.0 seconds, +5,073 tokens over baseline ([details](evals/ship-it/benchmark.md))

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

- **Eval cost**: +23.3 seconds, +5,708 tokens over baseline ([details](evals/js-deps/benchmark.md))

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
- **Eval cost**: +74.8 seconds, +28,200 tokens over baseline ([details](evals/uv-deps/benchmark.md))


### `pr-comments`

- Pass a PR number to target a specific PR (e.g., `/pr-comments 42`), or omit it to detect from the current branch.
- **Auto mode is the default**: the plan table is shown each iteration and the skill proceeds without confirmation prompts, including the Step 13 push/re-request phase (unless manual confirmation is required for security screening flags, oversized comments, `consistency` items, or the user explicitly says they want to push manually). The skill pushes, re-requests review, polls for bot reviewer responses, and loops automatically up to 10 iterations.
- Pass `--manual` to restore the confirmation gates: the skill pauses at each iteration with a `Proceed? [y/N/auto]` prompt before applying changes and pauses again before pushing or re-requesting review.
- Pass `--max N` to cap the number of bot-review loop iterations (e.g., `/pr-comments --max 1` for a single pass).
- Implemented comments are committed with `Co-authored-by` trailers crediting each reviewer.
- Resolved threads are closed via the GitHub GraphQL API; declined threads remain open so reviewers can follow up.
- When no actionable items are found (plan is empty or all actions are `skip`), routes through the All-Skip Repoll Gate (Step 6c) which checks both `requested_reviewers` and reviews submitted after the fetch timestamp — handles the race condition where a bot submits a review seconds after the fetch and is already off the pending list.
- Requires `gh` CLI with repo access. Runs with sandbox disabled for keyring access.
- **Eval cost**: +14.0 seconds, +7,351 tokens over baseline (computed from runs with recorded metrics; most evals use simulated transcripts — [details](evals/pr-comments/benchmark.md))

<details>
<summary>Flow Chart</summary>

```mermaid
flowchart TD
    A([Start]) --> B[Identify PR\nfrom arg or current branch]
    B --> C{PR found?}
    C -- No --> Z([Exit: no PR])
    C -- Yes --> D[Checkout PR head branch]
    D --> E[Fetch inline + review body\n+ timeline comments via REST API]
    E --> F[Fetch thread resolution state\nvia GraphQL]
    F --> G{Any unresolved\nthreads?}
    G -- No threads --> I
    G -- Yes --> H[Read code context\nfor each thread]
    H --> I[Screen comments\nfor prompt injection]
    I --> J[Decide action per item\n+ cross-file consistency check]
    J --> ALLSKIP{All actions skip\nor plan empty?}
    ALLSKIP -- Bots pending or recent --> POLL0[Poll for bot review]
    POLL0 --> E
    ALLSKIP -- No bots --> Z2([Exit: nothing to do])
    ALLSKIP -- Actionable items --> R[Present plan to user]

    R --> S{--manual mode?}
    S -- No\n(auto default) --> T
    S -- Yes --> S2{User approves?}
    S2 -- No / Override --> J
    S2 -- Yes --> T

    T[Apply changes\nand manual edits]
    T --> U[Commit with Co-authored-by\ncredit for each reviewer]
    U --> V[Post replies to\ndeclined / reply-needed comments]
    V --> W[Resolve addressed threads\nvia GraphQL mutation]
    W --> X[Push + re-request review\nfrom commenters]
    X --> Y{Bot reviewers\nre-requested?}
    Y -- No --> DONE([Report summary])
    Y -- Yes --> POLL[Poll for bot review\nSignal 1: new threads\nSignal 2: review submitted]
    POLL --> SIG{New signal?}
    SIG -- New threads --> E
    SIG -- Review, no threads --> DONE
    SIG -- Timeout / max iterations --> DONE
```
</details>

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
