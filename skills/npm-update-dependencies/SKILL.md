---
skill: npm-update-dependencies
description: Update npm packages to latest versions with validation and create PR
arguments: specific packages, glob pattern, or '.' for all
---

# Update Dependencies: $ARGUMENTS

Updates npm packages to their latest versions with automated testing and validation in an isolated worktree, then creates a pull request for review.

## Arguments

- **Specific packages**: `jest @types/jest`
- **All packages**: `.`
- **Glob patterns**: `@testing-library/* jest*`

## Process

### 1. Create Isolated Worktree

```bash
WORKTREE_NAME="npm-update-$(date +%Y%m%d-%H%M%S)"
WORKTREE_PATH="../$WORKTREE_NAME"
git worktree add "$WORKTREE_PATH" -b "$WORKTREE_NAME"
cd "$WORKTREE_PATH"
```

### 2. Identify Packages

- Parse `$ARGUMENTS` to determine packages
- For globs, expand against package.json dependencies
- For `.`, update all packages

### 3. Check and Update Versions

```bash
# Check latest version
npm view <package> version

# Prefer LTS when available
npm view <package> dist-tags

# Update packages
npm install <package>@latest
```

### 4. Run Security Audit

```bash
npm audit
npm audit fix
```

### 5. Validate Updates

Run in order, continue on failure to collect all errors:

```bash
npm run build
npm run lint
npm test
```

### 6. Handle Results

**On success:**
- Create commit with version changes
- Push branch to remote:
  ```bash
  git push -u origin "$WORKTREE_NAME"
  ```
- Check for existing dependency update PRs:
  ```bash
  gh pr list --search "chore: Update npm dependencies" --state open
  ```
- Create PR using gh CLI:
  ```bash
  gh pr create --title "chore: Update npm dependencies" --body "$(cat <<'EOF'
  ## Summary
  - Updated packages: [list major version changes]
  - Breaking changes fixed: [list code modifications]

  ## Validation Results
  | Check | Status |
  |-------|--------|
  | Build | ✅/❌ |
  | Lint | ✅/❌ |
  | Tests | ✅/❌ |
  | Security Audit | X vulnerabilities |

  ## Files Changed
  - [list modified package.json files]

  🤖 Generated with [Claude Code](https://claude.com/claude-code)
  EOF
  )"
  ```
- Return the PR URL to the user

**On failure:**
- Categorize errors (build/lint/test/audit)
- Provide specific remediation steps
- Offer options: isolate problem, revert specific updates, or abandon
- If partially successful, still create PR with failing checks noted

### 7. Update Documentation for Major Version Changes

When packages have major version upgrades (e.g., 18.x → 19.x, 4.x → 5.x):

1. **Identify major version changes** from the update:
   ```bash
   # Compare old vs new versions in package.json changes
   git diff --cached package.json | grep -E '^\+.*"version"'
   ```

2. **Search for version references in documentation**:
   ```bash
   # Search markdown files for version patterns
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
   - `React 18` → `React 19`
   - `Next.js 14` → `Next.js 16`
   - `Express 4.18` → `Express 5.x`
   - `Prisma 5.8` → `Prisma 7.x`

6. **Include in PR description**:
   ```markdown
   ## Documentation Updates
   - Updated version references in X files
   - [list files with changes]
   ```

### 8. Cleanup

```bash
git worktree remove "$WORKTREE_PATH"
# Note: Don't delete the branch - it's needed for the open PR
```

## Error Categories

| Category | Examples | Remediation |
|----------|----------|-------------|
| Build | Type errors, missing dependencies | Update @types/*, check changelogs |
| Lint | Code style issues | Run `npm run lint -- --fix` |
| Test | Breaking API changes | Review migration guides |
| Audit | Vulnerabilities | Manual remediation steps |

## Edge Cases

- No package.json: Error with clear message
- Not a git repo: Error - worktree requires git
- Package not found: Suggest checking package name
- Glob matches nothing: Warn and list available packages
