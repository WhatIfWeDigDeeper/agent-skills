---
name: ship-it
description: Create branch, commit, push, and open a pull request
arguments: optional branch name or PR title
---

# Ship: Branch, Commit, Push & PR

Create a branch (if needed), commit all changes, push, and open a pull request in one flow.

## Process

### 1. Check Current State

```bash
git status
git branch --show-current
git remote show origin | grep 'HEAD branch'
git diff --stat
git diff --stat --cached
```

Determine:
- What is the default branch? (detect from remote, do not assume `main`)
- Are there changes to commit? (If no staged or unstaged changes, abort with message)
- Are we on the default branch? (If so, need to create a branch)
- Are we already on a feature branch?

### 2. Create Branch (if on default branch)

If currently on the default branch, create and switch to a new branch:

```bash
git checkout -b <branch-name>
```

**Branch naming:**
- If user provided `$ARGUMENTS`, derive branch name from it (kebab-case, e.g. `fix/handle-null-response`)
- Otherwise, analyze the changes and generate a descriptive branch name
- Use prefixes: `feat/`, `fix/`, `refactor/`, `docs/`, `chore/`, `test/` based on change type

### 3. Stage & Commit

```bash
git add -A
```

Analyze the diff and generate a commit message:

**Format:** `type: concise description`

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `refactor`: Code restructuring
- `docs`: Documentation
- `test`: Tests
- `chore`: Maintenance

```bash
git commit -m "type: description"
```

If the agent supports co-authorship attribution (e.g., `Co-Authored-By`), append it per the agent's conventions.

If user provided `$ARGUMENTS` that looks like a commit message, use it as the commit message.

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

Generate the PR and create it:

```bash
gh pr create --title "<title>" --body "<body>"
```

**PR body format:**
```markdown
## Summary
- [2-3 bullet points describing the changes]

## Test Plan
- [ ] [How to test these changes]

---
🤖 Generated with [agent name and link, per agent conventions]
```

**Title:** If user provided `$ARGUMENTS`, use as PR title. Otherwise generate from the commit(s).

### 6. Report

Output:
- Branch name
- Commit hash and message
- PR URL

## Rules

- Keep commit subject line under 50 characters
- Keep PR title under 70 characters
- Use imperative mood ("add" not "added")
- Don't commit files that look like secrets (.env, credentials, keys)
- If a PR already exists for this branch, show the existing PR URL instead of creating a duplicate
- If there are merge conflicts with the default branch, warn the user before creating the PR
