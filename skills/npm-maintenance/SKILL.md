---
name: npm-maintenance
description: Maintain npm packages through security audits or dependency updates in an isolated git worktree. Use for: (1) Security requests - audit, CVE, vulnerabilities, fix security issues, check for vulnerable dependencies; (2) Update requests - update dependencies, upgrade packages, get latest versions, modernize npm dependencies.
---

# NPM Maintenance

Manages npm package maintenance tasks in an isolated worktree, including security audits and dependency updates.

## Arguments

- **Specific packages**: `jest @types/jest`
- **All packages**: `.`
- **Glob patterns**: `@testing-library/* jest*`

## Workflow Selection

Based on user request:
- **Security audit** (audit, CVE, vulnerabilities, security): Read [references/audit-workflow.md](references/audit-workflow.md)
- **Dependency updates** (update, upgrade, latest, modernize): Read [references/update-workflow.md](references/update-workflow.md)

## Shared Process

### 1. Create Isolated Worktree

```bash
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
WORKTREE_NAME="npm-maintenance-$TIMESTAMP"
WORKTREE_PATH="../$WORKTREE_NAME"
git worktree add "$WORKTREE_PATH" -b "$WORKTREE_NAME"
cd "$WORKTREE_PATH"
```

### 2. Discover Package Locations

Find all package.json files excluding node_modules:
```bash
find . -name "package.json" -not -path "*/node_modules/*" -type f
```

Store results as an array of directories to process.

### 3. Identify Packages

- Parse `$ARGUMENTS` to determine packages
- For globs, expand against package.json dependencies
- For `.`, process all packages

### 4. Validate Changes

Check `package.json` scripts for available validation commands:

| Purpose | Common names |
|---------|--------------|
| Build | `build`, `compile`, `tsc` |
| Lint | `lint`, `check`, `eslint` |
| Test | `test`, `jest`, `vitest` |

Run available scripts in order (build → lint → test), continuing on failure to collect all errors. Skip any that don't exist.

If validation fails, revert to previous version before continuing.

### 5. Update Documentation for Major Version Changes

For major version upgrades (e.g., 18.x to 19.x):

1. Search for version references: `grep -r "React 18\|Express 4" --include="*.md" .`
2. Update in: `CLAUDE.md`, `README.md`, `docs/*.md`
3. Skip: `specs/*/research.md`, `specs/*/tasks.md`, archived files
4. Include changes in report/PR description

### 6. Cleanup

```bash
git worktree remove "$WORKTREE_PATH"
# Delete branch only if no PR was created
git branch -d "$WORKTREE_NAME"
```

## Edge Cases

- No package.json: Error with clear message
- Not a git repo: Error - worktree requires git
- Package not found: Suggest checking package name
- Glob matches nothing: Warn and list available packages
