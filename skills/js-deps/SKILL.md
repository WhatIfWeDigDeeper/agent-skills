---
name: js-deps
description: >
  Maintain JavaScript/Node.js packages through security audits or dependency updates in an isolated git worktree.
  Supports npm, yarn, pnpm, and bun. Use for: (1) Security requests - audit, CVE, vulnerabilities, fix security issues,
  check for vulnerable dependencies; (2) Update requests - update dependencies, upgrade packages, get latest versions,
  modernize dependencies; (3) when user types "/js-deps" with or without specific package names or glob patterns.
arguments: >
  Specific package names (e.g., "jest @types/jest"), "." for all packages,
  or glob patterns (e.g., "@testing-library/* jest*")
---

# JS Deps

## Workflow Selection

Based on user request:
- **Security audit** (audit, CVE, vulnerabilities, security): Read [references/audit-workflow.md](references/audit-workflow.md)
- **Dependency updates** (update, upgrade, latest, modernize): Read [references/update-workflow.md](references/update-workflow.md)

## Shared Process

### 1. Create Isolated Environment

**Preferred: Worktree** (isolated, non-disruptive)
```bash
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
BRANCH_NAME="js-deps-$TIMESTAMP"
WORKTREE_PATH="../$BRANCH_NAME"
git worktree add "$WORKTREE_PATH" -b "$BRANCH_NAME"
cd "$WORKTREE_PATH"
USE_WORKTREE=true
```

**Fallback: Branch** (if worktree fails due to sandbox directory restrictions)

Prompt user: "Worktree creation failed (sandbox may restrict creating directories outside the working directory). Run in current directory on a new branch instead? This will stash any uncommitted changes."

If user accepts:
```bash
git stash --include-untracked
git checkout -b "$BRANCH_NAME"
USE_WORKTREE=false
```

### 2. Detect Package Manager

Detect from lock files and `package.json` `packageManager` field (which takes precedence). See [references/package-managers.md](references/package-managers.md) for detection logic and command mappings.

### 3. Verify Registry Access

Verify the package manager CLI is available and, for npm, that it can reach the registry. See [references/package-managers.md](references/package-managers.md) for manager-specific verification commands.

If verification fails, prompt user: "Cannot reach package registry. Sandbox may be blocking network access. To allow package manager commands in sandbox mode, update settings.json."

Do not proceed until verification passes.

### 4. Discover Package Locations

Find all `package.json` files excluding `node_modules`. Store results as an array of directories to process.

### 5. Install Dependencies

Install dependencies in each discovered package directory so that `npm outdated` (and similar commands) can accurately compare installed versions against the registry. Without `node_modules`, exact-pinned packages (no `^` or `~`) won't appear in outdated reports.

### 6. Identify Packages

- Parse `$ARGUMENTS` to determine packages
- For globs, expand against package.json dependencies
- For `.`, process all packages

### 7. Validate Changes

Check `package.json` scripts for available validation commands. Run available scripts using `$PM run <script>` in order (build, lint, test), continuing on failure to collect all errors. Skip any that don't exist.

If validation fails, revert the failing package to its previous version before continuing with remaining packages:
```bash
git checkout -- package.json package-lock.json  # or the equivalent lock file
$PM install
```

### 8. Update Documentation for Major Version Changes

For major version upgrades (e.g., 18.x to 19.x):

1. Search for version references in markdown files
2. Update in: `CLAUDE.md`, `README.md`, `docs/*.md`
3. Include changes in report/PR description

### 9. Cleanup

**If using worktree:**
```bash
cd -
git worktree remove "$WORKTREE_PATH"
# Delete branch only if no PR was created
git branch -d "$BRANCH_NAME"
```

**If using branch fallback:**
```bash
git checkout -
git stash pop
# Delete branch only if no PR was created
git branch -d "$BRANCH_NAME"
```

## Edge Cases

- **Glob matches nothing**: Warn and list available packages
- **Network restricted**: Package manager commands require internet access; will fail in offline sandbox environments
- **Unsupported package manager**: Prompt user for guidance
