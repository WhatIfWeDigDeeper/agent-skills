# Security Audit Workflow

Use the detected `$PM` package manager for all commands. See [package-managers.md](package-managers.md) for command mappings.

## Audit Execution

### Run Security Audit on Each Directory

For each directory containing package.json:
```bash
cd "$WORKTREE_PATH/<directory>"
AUDIT_JSON=$($PM audit --json 2>/dev/null)
# Write to temp file if you need to inspect: echo "$AUDIT_JSON" > "$TMPDIR/audit-report-<dir-name>.json"
```

Note: bun does not support audit. If using bun, skip audit and inform user.

**Note:** Installation (SKILL.md step 5) is not required before running `$PM audit` — the audit reads from lock files and package.json, not `node_modules`.

Collect all audit results into a consolidated report.

### Scope to Requested Packages

If `$ARGUMENTS` contains specific package names or glob patterns (not `.` or empty), filter the vulnerability list to only those packages before applying fixes.

### Categorize by Severity

Parse audit results for each directory:

| Severity | Action |
|----------|--------|
| Critical | Immediate action required |
| High | Serious risk, patch ASAP |
| Moderate | Should fix soon |
| Low | Fix when convenient |

### Determine Strategy

Always update packages **sequentially within a directory** to avoid lock file races — concurrent installs in the same directory will corrupt `package-lock.json` (or equivalent).

Parallelize **across directories** only: if multiple directories have vulnerabilities, launch a separate Task subagent (general-purpose, background) per directory. Each subagent handles package updates and validation for its directory only — **do not commit from subagents**. The main agent commits all changes after all subagents complete.

When consolidating results:
- Collect vulnerability counts (before/after), packages fixed, and validation results from each subagent
- Merge into a single report; if any subagent fails, still include partial results from the others
- If a subagent fails to fix a package, document it in the PR as a partial fix

### Update Packages

#### Preferred: Use audit fix (npm only)

For npm, try automated fix first:
```bash
cd "$WORKTREE_PATH/<directory>"
npm audit fix
```
This handles transitive dependency chains automatically. Only proceed to manual updates below if `npm audit fix` reports remaining vulnerabilities or if using yarn/pnpm/bun.

For each vulnerable package in each directory, use the appropriate install command from [package-managers.md](package-managers.md):
```bash
cd "$WORKTREE_PATH/<directory>"
# npm:
npm install <package>@<patched-version>
# yarn, pnpm, bun:
$PM add <package>@<patched-version>
```

Use the minimum patched version from the audit report's `fixAvailable.version` field. Only fall back to `@latest` if the audit report explicitly recommends it as the fix.

Validate after each update per SKILL.md step 7.

### Post-Audit Scan

For each directory:
```bash
cd "$WORKTREE_PATH/<directory>"
$PM audit
```

Compare before/after vulnerability counts per directory.

## Handle Results

### On Success

1. Generate consolidated security report
2. Create commit with security fixes
3. Push branch to remote:
   ```bash
   git push -u origin "$BRANCH_NAME"
   ```
4. Create PR using gh CLI. Write the PR body to a temp file first (heredocs may fail in sandboxed environments):
   ```bash
   BODY_FILE=$(mktemp)
   cat > "$BODY_FILE" << 'PREOF'
   ## Summary
   - Vulnerabilities fixed: [count]
   - Remaining vulnerabilities: [count with reasons]

   ## Changes by Directory
   [list directories and packages updated]

   ## Validation Results
   | Check | Status |
   |-------|--------|
   | Build | pass/fail |
   | Lint | pass/fail |
   | Tests | pass/fail |
   | Security Audit | X remaining |

   Generated with [Claude Code](https://claude.com/claude-code)
   PREOF
   gh pr create --title "fix: resolve security vulnerabilities" --body-file "$BODY_FILE"
   rm -f "$BODY_FILE"
   ```
5. Return the PR URL to the user

### On Failure

- Categorize by directory and package
- Provide specific remediation steps for unfixable vulnerabilities
- If partially successful, still create PR with remaining issues noted

### Upstream-Unfixable Vulnerabilities

When transitive dependencies have vulnerabilities that no direct dependency update can resolve:

1. Check if the project uses `audit-ci` or similar CI audit tools (look for `audit-ci.json`, `audit-ci.jsonc`, or audit scripts in `package.json`)
2. If so, add the advisory ID (e.g., `GHSA-xxxx-xxxx-xxxx`) to the `allowlist` array in each package's audit config
3. Document the upstream blockers in the PR description — list which packages hold the vulnerable transitive dependency and why no fix is available
4. Include the allowlist change in the same commit/PR as the fixable updates
