---
skill: npm-audit-and-fix
description: Security audit with automatic fixes for vulnerabilities across all package.json files
arguments: package names, glob pattern, or '.' for all
---

# Security Audit: $ARGUMENTS

Scan for vulnerabilities and automatically fix them across all package.json files in an isolated worktree.

## Process

### 1. Create Isolated Worktree

```bash
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
WORKTREE_PATH="../audit-fix-$TIMESTAMP"
git worktree add "$WORKTREE_PATH" -b "security-audit-$TIMESTAMP"
cd "$WORKTREE_PATH"
```

### 2. Discover All package.json Files

Find all package.json files excluding node_modules:
```bash
find . -name "package.json" -not -path "*/node_modules/*" -type f
```

Store results as an array of directories to audit.

### 3. Run Security Audit on Each Directory

For each directory containing package.json:
```bash
cd <directory>
npm audit --json > audit-report-<dir-name>.json
```

Collect all audit results into a consolidated report.

### 4. Categorize by Severity

Parse audit results for each directory:
- **Critical**: Immediate action required
- **High**: Serious risk, patch ASAP
- **Moderate**: Should fix soon
- **Low**: Fix when convenient

### 5. Determine Strategy

Per directory:
- **1-3 packages**: Update sequentially
- **4+ packages**: Use parallel Task subagents (2 packages per agent)

If multiple directories have vulnerabilities, process them in parallel using separate agents.

### 6. Update Packages

For each vulnerable package in each directory:
```bash
cd <directory>
npm install <package>@latest
```

Then validate (if scripts exist):
```bash
npm run build && npm run lint && npm test
```

If validation fails, revert to previous version.

### 7. Post-Audit Scan

For each directory:
```bash
cd <directory>
npm audit
```

Compare before/after vulnerability counts per directory.

### 8. Report and Prompt

Generate consolidated security report with:
- Vulnerabilities per directory (initial vs remaining)
- Successfully updated packages per directory
- Failed updates with reasons
- Recommendations for remaining issues
- Overall project security status

Prompt: merge fixes, keep for review, or discard.

### 9. Update Documentation for Major Version Changes

When security fixes require major version upgrades:

1. **Identify major version changes** across all directories:
   - Track packages that jumped major versions (e.g., 4.x → 5.x)

2. **Search for version references**:
   ```bash
   grep -r "Express 4\|Prisma 5\|React 18" --include="*.md" .
   ```

3. **Update documentation files** (prioritized):
   - `CLAUDE.md` - Active technologies
   - `README.md` - Stack descriptions
   - `docs/*.md` - Version tables and tech stack sections

4. **Skip historical documents**:
   - `specs/*/research.md`
   - `specs/*/tasks.md`

5. **Include in security report**:
   ```
   Documentation Updates
   ---------------------
   Updated version references in:
   - CLAUDE.md (React 18 → 19)
   - docs/API_IMPLEMENTATION_SUMMARY.md (Express 4.18 → 5.x)
   ```

### 10. Cleanup

```bash
git worktree remove "$WORKTREE_PATH"
git branch -d "security-audit-$TIMESTAMP"
```

## Parallel Execution

### Per-Directory Parallelization
When multiple directories have vulnerabilities, launch separate Task subagents for each:

```
Task({
  subagent_type: 'general-purpose',
  prompt: 'Audit and fix vulnerabilities in <directory>...',
  run_in_background: true
})
```

### Per-Package Parallelization
Within a directory with >3 vulnerable packages, split into groups:

```
Task({
  subagent_type: 'general-purpose',
  prompt: 'Update packages X, Y in <directory> with full validation...',
  run_in_background: true
})
```

Collect results from all agents before generating final report.

## Example Output

```
Security Audit Report
=====================

Scanned Directories: 5
- /api (Express + Prisma)
- /koa-api (Koa + PostgreSQL)
- /hono-api (Hono + Drizzle)
- /parse-server-api (Parse Server)
- /ui (React UI)

Results by Directory:
---------------------

/api: 2 vulnerabilities fixed
  ✓ express 4.17.1 → 4.18.2 (moderate)
  ✓ jsonwebtoken 8.5.1 → 9.0.0 (high)

/ui: No vulnerabilities found

/koa-api: 1 vulnerability (could not fix)
  ✗ koa-router 10.0.0 (no fix available)

Overall: 2/3 vulnerabilities fixed
```
