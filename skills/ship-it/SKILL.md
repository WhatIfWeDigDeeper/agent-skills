---
name: ship-it
description: >-
  Create branch, commit, push, and open a pull request in one flow.
  Use when: user says "ship it", "ship this", "send it", "create a PR",
  "push and PR", or wants to go from uncommitted changes to an open
  pull request in a single step.
license: MIT
metadata:
  author: Gregory Murray
  repository: github.com/whatifwedigdeeper/agent-skills
  version: "0.1"
---

# Ship: Branch, Commit, Push & PR

Create a branch (if needed), commit all changes, push, and open a pull request in one flow.

`$ARGUMENTS`: optional text passed when invoking the skill (e.g., `/ship-it fix login timeout`). Used to derive branch name, commit message, or PR title.

## Process

### 1. Preflight Checks

```bash
git status
git branch --show-current
git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@'
git diff --stat
git diff --stat --cached
gh auth status
```

Determine:
- What is the default branch? (detect from remote ref, do not assume `main`)
- Are there changes to commit? (If no staged or unstaged changes, abort with message)
- Are we on the default branch? (If so, need to create a branch)
- Are we already on a feature branch?
- Is `gh` CLI installed and authenticated? (If not, abort: "Install and authenticate the GitHub CLI: https://cli.github.com")
- Are we in detached HEAD state? (If so, create a branch before proceeding)

### 2. Create Branch (if needed)

**Already on a feature branch?** Skip this step entirely — use the current branch.

If on the default branch or in detached HEAD, create and switch to a new branch:

```bash
git checkout -b <branch-name>
```

**Branch naming:**
- If user provided `$ARGUMENTS`, derive branch name from it (kebab-case, e.g. `fix/handle-null-response`)
- Otherwise, analyze the changes and generate a descriptive branch name
- Use prefixes: `feat/`, `fix/`, `refactor/`, `docs/`, `chore/`, `test/` based on change type
- If a remote branch with the same name already exists, append a short suffix (e.g. `-2`)

### 3. Stage & Commit

Stage specific files rather than using `git add -A`. Review the changed files list and exclude:
- Secret files: `.env`, `.env.*`, credentials, private keys, tokens
- Large binaries or build artifacts

```bash
git add <file1> <file2> ...
git diff --cached --name-only
```

Review the staged file list before committing. If any files look like secrets or shouldn't be committed, unstage them and warn the user.

Analyze the diff and generate a conventional commit message:

**Format:** `type: concise description` (e.g., `feat: add OAuth login flow`)

```bash
git commit -m "type: description"
```

If the agent supports co-authorship attribution (e.g., `Co-Authored-By`), append it per the agent's conventions. If user provided `$ARGUMENTS` that looks like a commit message, use it as the commit message.

### 4. Push

```bash
git push -u origin <branch-name>
```

### 5. Create Pull Request

Gather context for the PR description:

```bash
git log <default-branch>..HEAD --oneline
git diff <default-branch>..HEAD --stat
```

Check for an existing PR on this branch:

```bash
gh pr view --json url 2>/dev/null
```

**If a PR already exists:** report its URL, skip creation, and jump to Step 6.

Otherwise, create the PR:

```bash
gh pr create --title "<title>" --body "$(cat <<'EOF'
## Summary
- [2-3 bullet points describing the changes]

## Test Plan
- [ ] [How to test these changes]

---
🤖 Generated with [agent name and link, per agent conventions]
EOF
)"
```

**Title:** If user provided `$ARGUMENTS`, use as PR title. Otherwise generate from the commit(s).

### 6. Report

Output:
- Branch name
- Commit hash and message
- PR URL

## Rules

- Keep commit subject line under 72 characters
- Keep PR title under 70 characters
- Use imperative mood ("add" not "added")
- Never commit files that look like secrets (.env, credentials, keys)
- If there are merge conflicts with the default branch, warn the user before creating the PR
