---
name: npm-maintenance
description: Maintain npm packages through security audits or dependency updates. Use for security-related requests (audit, CVE, vulnerabilities, security issues) or update requests (update dependencies, upgrade packages, latest versions).
arguments: Package names, glob patterns (e.g., `@prisma/*`), or `.` for all packages
---

# NPM Maintenance

Manages npm package maintenance tasks in an isolated worktree, including security audits and dependency updates.

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

Run in order after each update, continue on failure to collect all errors:

```bash
npm run build
npm run lint
npm test
```

If validation fails, revert to previous version before continuing.

### 5. Update Documentation for Major Version Changes

When packages have major version upgrades (e.g., 18.x to 19.x, 4.x to 5.x):

1. **Identify major version changes** from the update:
   - Track packages that jumped major versions

2. **Search for version references in documentation**:
   ```bash
   grep -r "React 18\|Next.js 14\|Express 4\|Prisma 5" --include="*.md" .
   ```

3. **Files to check** (prioritized):
   - `CLAUDE.md` - Active technologies section
   - `README.md` - Stack descriptions
   - `docs/*.md` - Implementation docs with version tables
   - `specs/*/plan.md` - Technical context sections

4. **Skip historical documents** (don't update):
   - `specs/*/research.md` - Original research notes
   - `specs/*/tasks.md` - Completed task records
   - Files with "historical" or "archive" in path

5. **Update pattern**: Replace version references like:
   - `React 18` to `React 19`
   - `Express 4.18` to `Express 5.x`

6. **Include in report/PR description**:
   ```
   Documentation Updates
   ---------------------
   Updated version references in:
   - CLAUDE.md (React 18 to 19)
   - docs/API_IMPLEMENTATION_SUMMARY.md (Express 4.18 to 5.x)
   ```

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
