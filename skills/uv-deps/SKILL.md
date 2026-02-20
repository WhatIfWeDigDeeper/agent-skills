---
name: uv-deps
description: >
  Maintain Python packages through security audits or dependency updates on a dedicated branch using uv.
  Use for: security audits, CVE fixes, vulnerability checks, dependency updates, package upgrades,
  outdated packages, bump versions, fix Python vulnerabilities, check for Python CVEs, audit Python packages,
  update pyproject.toml dependencies, modernize Python deps, or when user types "/uv-deps" with or without
  specific package names or glob patterns. Use "help" or "--help" to show options.
license: MIT
compatibility: Requires git, uv, Python 3.12+, and network access to PyPI
metadata:
  author: Gregory Murray
  repository: github.com/whatifwedigdeeper/agent-skills
  version: "0.1"
---

# UV Deps

## Arguments

Specific package names (e.g. `fastapi asyncpg`), `.` for all packages, or glob patterns (e.g. `django-*`).

If `$ARGUMENTS` is `help`, `--help`, `-h`, or `?`, skip the workflow and read [references/interactive-help.md](references/interactive-help.md).

## Workflow Selection

Based on user request:
- **Security audit** (audit, CVE, vulnerabilities, security): Read [references/audit-workflow.md](references/audit-workflow.md)
- **Dependency updates** (update, upgrade, latest, modernize): Read [references/update-workflow.md](references/update-workflow.md)
- **Ambiguous** (no clear intent, or invoked with no args): Read [references/interactive-help.md](references/interactive-help.md)

## Shared Process

### 1. Create Branch

Stash uncommitted changes and create a dedicated branch. Track whether a stash was actually created:
```bash
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
BRANCH_NAME="py-uv-deps-$TIMESTAMP"
STASH_BEFORE=$(git stash list | wc -l)
git stash --include-untracked
STASH_AFTER=$(git stash list | wc -l)
STASH_CREATED=$( [ "$STASH_AFTER" -gt "$STASH_BEFORE" ] && echo true || echo false )
git checkout -b "$BRANCH_NAME"
```

### 2. Verify Tool Access

Verify that `uv` and `uvx` are available and can reach PyPI. See [references/uv-commands.md](references/uv-commands.md) for verification commands and troubleshooting.

All `uv`, `uvx`, `gh`, `git push`, and `git commit` commands require `dangerouslyDisableSandbox: true`.

Do not proceed until verification passes.

### 3. Discover Python Projects

This skill targets `pyproject.toml`-based projects managed by uv. Projects using only `requirements.txt`, `setup.py`, or other package managers (poetry, pipenv) are out of scope.

Find all directories containing `pyproject.toml` with a `[project.dependencies]`, `[project.optional-dependencies]`, or `[dependency-groups]` section, excluding `.venv`, `.tox`, `build`, and `dist` directories. Store results as an array of directories to process. If none found, report to user and skip to cleanup.

For workspaces (`[tool.uv.workspace]` in root `pyproject.toml`), run `uv sync` and `uv lock` from the workspace root — the root `uv.lock` covers all members.

### 4. Sync Dependencies

Sync before identifying packages so that version checks are accurate. For each discovered project directory: Check `pyproject.toml` to determine which dev dependency pattern the project uses:
- If `[project.optional-dependencies]` has a `dev` key: use `uv sync --extra dev`
- If `[dependency-groups]` has a `dev` key (PEP 735): use `uv sync --group dev`
- If neither exists: use `uv sync`

See [references/uv-commands.md](references/uv-commands.md) for full command reference.

### 5. Identify Packages

- Parse `$ARGUMENTS` to determine packages
- For `.`, process all dependencies from `[project.dependencies]`, `[project.optional-dependencies]`, and `[dependency-groups]`
- For globs (e.g. `django-*`), expand against all dependency sections
- For specific names, validate they exist in `[project.dependencies]`, `[project.optional-dependencies]`, or `[dependency-groups]`
- Warn if a package name or glob matches nothing and list available packages

### 6. Validate Changes

Run available validation tools per [references/uv-commands.md](references/uv-commands.md). Continue on failure to collect all errors.

If validation fails for a specific package update, revert before continuing with remaining packages (replace `<directory>` with the actual project path):
```bash
git checkout -- pyproject.toml
git checkout -- uv.lock 2>/dev/null || true  # uv.lock may not be committed
uv sync  # run from project directory
```

### 7. Commit Changes

After all updates are validated, check whether `uv.lock` is tracked in git, then commit:

```bash
# Check if uv.lock is gitignored
git check-ignore uv.lock && UV_LOCK_IGNORED=true || UV_LOCK_IGNORED=false

git add pyproject.toml
[ "$UV_LOCK_IGNORED" = "false" ] && git add uv.lock
# For workspaces, also add member pyproject.toml files
git commit -m "<commit message from workflow>"
```

Commit message format:
- Security audit: `fix: patch vulnerable Python dependencies`
- Dependency update: `chore: update Python dependencies`

### 8. Cleanup

If a PR was created, do not delete the branch — it's needed for the open PR.

```bash
git checkout -
[ "$STASH_CREATED" = "true" ] && (git stash pop || echo "Stash pop had conflicts, resolve manually")
# Only delete branch if no PR was created (requires dangerouslyDisableSandbox: true)
if ! gh pr list --head "$BRANCH_NAME" --json url --jq '.[0].url' | grep -q .; then
  git branch -d "$BRANCH_NAME"
fi
```

## Edge Cases

- **Unknown package arguments**: If a package from `$ARGUMENTS` is not found in any `pyproject.toml` section, warn and list available packages
- **Resolver conflicts after major upgrades**: When upgrading causes dependency conflicts (e.g., package A requires `foo<2.0` but package B needs `foo>=2.0`), document the conflict, offer to skip or add a version constraint, and continue with remaining packages
- **Dev dependency placement**: After adding dev packages, verify they landed in `[project.optional-dependencies]` or `[dependency-groups]`, not `[project.dependencies]`
- **Lockfile sync**: After all pyproject.toml changes, run `uv sync` to regenerate `uv.lock` and commit both files
