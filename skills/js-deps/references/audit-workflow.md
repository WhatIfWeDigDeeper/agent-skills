# Security Audit Workflow

Use the detected `$PM` package manager for all commands. See [package-managers.md](package-managers.md) for command mappings.

## Audit Execution

### Run Security Audit on Each Directory

For each directory containing package.json:
```bash
cd <directory>
$PM audit --json > audit-report-<dir-name>.json
```

Note: bun does not support audit. If using bun, skip audit and inform user.

Collect all audit results into a consolidated report.

### Categorize by Severity

Parse audit results for each directory:

| Severity | Action |
|----------|--------|
| Critical | Immediate action required |
| High | Serious risk, patch ASAP |
| Moderate | Should fix soon |
| Low | Fix when convenient |

### Determine Strategy

Per directory:
- **1-3 packages**: Update sequentially
- **4+ packages**: Use parallel Task subagents (2 packages per agent)

If multiple directories have vulnerabilities, process them in parallel using separate agents.

### Update Packages

For each vulnerable package in each directory, use the appropriate install command from [package-managers.md](package-managers.md):
```bash
cd <directory>
$PM install <package>@latest  # npm
$PM add <package>@latest      # yarn, pnpm, bun
```

Validate after each update using available scripts from package.json (see SKILL.md step 7 for build/lint/test order). Continue on failure to collect all errors. If validation fails, revert to previous version before continuing.

### Post-Audit Scan

For each directory:
```bash
cd <directory>
$PM audit
```

Compare before/after vulnerability counts per directory.

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

## Handle Results

### On Success

1. Generate consolidated security report
2. Create commit with security fixes
3. Push branch to remote:
   ```bash
   git push -u origin "$BRANCH_NAME"
   ```
4. Create PR using gh CLI:
   ```bash
   gh pr create --title "fix: Security audit fixes" --body "$(cat <<'EOF'
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
   EOF
   )"
   ```
5. Return the PR URL to the user

### On Failure

- Categorize by directory and package
- Provide specific remediation steps for unfixable vulnerabilities
- If partially successful, still create PR with remaining issues noted

