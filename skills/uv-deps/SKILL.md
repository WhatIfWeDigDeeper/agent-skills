---
name: uv-deps
description: Maintain Python packages through security audits or dependency updates using an isolated git worktree and uv. Use for security audits, CVE fixes, vulnerability checks, dependency updates, package upgrades, outdated packages, bump versions, fix Python vulnerabilities, check for Python CVEs, audit Python packages, update pyproject.toml dependencies, modernize Python deps, or when user types /uv-deps with or without specific package names or glob patterns.
license: MIT
compatibility: Requires git, uv, and network access to PyPI
metadata:
  author: Gregory Murray
  repository: github.com/whatifwedigdeeper/agent-skills
  version: "0.3"
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

### 1. Create Worktree

Create an isolated git worktree so the main working directory is never modified:
```bash
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
BRANCH_NAME="py-uv-deps-$TIMESTAMP"
WORKTREE_PATH="${TMPDIR:-/tmp}/$BRANCH_NAME"
git worktree add "$WORKTREE_PATH" -b "$BRANCH_NAME"
```

If `git worktree add` fails (e.g., sandbox permission error), prompt the user:
> `git worktree` requires write access to `$TMPDIR`. Choose an option:
> 1. Add `$TMPDIR` to your sandbox allowlist in `settings.json` (recommended)
> 2. Fall back to branch+stash approach

**All subsequent steps operate within `$WORKTREE_PATH`.** Discovery, syncs, edits, and commits all happen there. Paths like `cd <directory>` in reference files are relative to `$WORKTREE_PATH`.

### 2. Verify Tool Access

Verify that `uv` and `uvx` are available and can reach PyPI. See [references/uv-commands.md](references/uv-commands.md) for verification commands and troubleshooting.

All `uv`, `uvx`, `gh`, `git push`, and `git commit` commands require `dangerouslyDisableSandbox: true`.

Do not proceed until verification passes.

### 3. Discover Python Projects

This skill targets `pyproject.toml`-based projects managed by uv. Projects using only `requirements.txt`, `setup.py`, or other package managers (poetry, pipenv) are out of scope.

Find all directories containing `pyproject.toml` within `$WORKTREE_PATH` with a `[project.dependencies]`, `[project.optional-dependencies]`, or `[dependency-groups]` section, excluding `.venv`, `.tox`, `build`, and `dist` directories. Store results as an array of directories to process. If none found, report to user and skip to cleanup.

For **uv workspaces** (root `pyproject.toml` contains `[tool.uv.workspace]`): treat the workspace root as the single project directory and do not process member subdirectories individually — the root `uv.lock` covers all members. Run `uv sync` and `uv lock` from the workspace root only.

### 4. Sync Dependencies

Sync before identifying packages so that version checks are accurate. For each discovered project directory: Check `pyproject.toml` to determine which dev dependency pattern the project uses:
- If `[project.optional-dependencies]` has a `dev` key: use `uv sync --extra dev`
- If `[dependency-groups]` has a `dev` key (PEP 735): use `uv sync --group dev`
- If neither exists: use `uv sync`

If `uv sync` fails (e.g., resolver conflicts, missing packages, unsupported Python version), report the error, skip this project directory, and continue with the remaining directories.

See [references/uv-commands.md](references/uv-commands.md) for full command reference.

### 5. Identify Packages

- Parse `$ARGUMENTS` to determine packages
- For `.`, process all dependencies from `[project.dependencies]`, `[project.optional-dependencies]`, and `[dependency-groups]`
- For globs (e.g. `django-*`), expand against all dependency sections
- For specific names, validate they exist in `[project.dependencies]`, `[project.optional-dependencies]`, or `[dependency-groups]`
- Warn if a package name or glob matches nothing and list available packages

### 6. Validate Changes

Detect available validators by checking `pyproject.toml` for `mypy`, `ruff`, and `pytest` in any dependency section. Run whichever are present via `uv run` (see [references/uv-commands.md](references/uv-commands.md) for commands). Prefer project task runners (Makefile, tox, nox) if present.

- **On overall validation failure**: continue running validation to collect all errors before reporting
- **On per-package failure after update**: revert that package before continuing with the next package (revert commands below)

If validation fails for a specific package update, revert before continuing with remaining packages (replace `<directory>` with the actual project path):
```bash
# Run from within $WORKTREE_PATH/<directory>
git checkout -- pyproject.toml
git checkout -- uv.lock 2>/dev/null || true  # uv.lock may not be committed
uv sync  # run from project directory
```

### 7. Commit Changes

After all updates are validated, check whether `uv.lock` is tracked in git, then commit:

```bash
# Run from $WORKTREE_PATH
# Check if uv.lock is tracked by git (if not, don't add it)
git ls-files --error-unmatch uv.lock > /dev/null 2>&1 && UV_LOCK_TRACKED=true || UV_LOCK_TRACKED=false

git add pyproject.toml
[ "$UV_LOCK_TRACKED" = "true" ] && git add uv.lock
# For workspaces, also stage any changed member pyproject.toml files
git diff --name-only | grep 'pyproject\.toml$' | xargs git add 2>/dev/null || true
git commit -m "<commit message from workflow>"
# If commit fails due to GPG keyring access, retry with --no-gpg-sign
```

Commit message format:
- Security audit: `fix: patch vulnerable Python dependencies`
- Dependency update: `chore: update Python dependencies`

### 8. Cleanup

Remove the worktree. The main working directory was never modified, so no stash restore is needed.

```bash
git worktree remove "$WORKTREE_PATH" --force
# Only delete branch if no PR was created (requires dangerouslyDisableSandbox: true)
PR_URL=$(gh pr list --head "$BRANCH_NAME" --json url --jq '.[0].url' 2>/dev/null)
if [ -z "$PR_URL" ]; then
  git branch -d "$BRANCH_NAME" 2>/dev/null || git branch -D "$BRANCH_NAME"
fi
```

`--force` handles cases where the skill failed mid-run with uncommitted changes in the worktree.

## Edge Cases

- **Resolver conflicts after major upgrades**: When upgrading causes dependency conflicts (e.g., package A requires `foo<2.0` but package B needs `foo>=2.0`), document the conflict, offer to skip or add a version constraint, and continue with remaining packages
- **Dev dependency placement**: After adding dev packages, verify they landed in `[project.optional-dependencies]` or `[dependency-groups]`, not `[project.dependencies]`
