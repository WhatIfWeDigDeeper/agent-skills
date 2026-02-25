# Dependency Update Workflow

Use the detected `$PM` package manager for all commands. See [package-managers.md](package-managers.md) for command mappings.

## Prerequisites

Ensure dependencies are installed first (SKILL.md step 5) so that `$PM outdated` can accurately compare installed vs. registry versions.

## Version Checking and Updates

### Discover What Needs Updating

Run the outdated check to get a list of packages to update. See [package-managers.md](package-managers.md) for the correct command per package manager.

Filter the results based on the version types selected by the user (major/minor/patch) if `help`/options were used.

### Check and Update Versions

Use the appropriate commands for your package manager (see [package-managers.md](package-managers.md)):

```bash
# Check latest version
$PM view <package> version   # npm, pnpm, yarn
bunx npm-view <package> version  # bun

# Prefer LTS when available
$PM view <package> dist-tags  # npm, pnpm, yarn
```

Use the install command from the **Install/Update** table in [package-managers.md](package-managers.md) — the command verb differs by manager (`npm install` vs `yarn/pnpm/bun add`).

### Run Security Audit

After updating, check for new vulnerabilities:
```bash
$PM audit
$PM audit fix  # npm only
```

For yarn, pnpm, and bun: `audit fix` is not available — fix remaining vulnerabilities manually using the steps in [audit-workflow.md](audit-workflow.md). Note: bun does not support audit at all; skip this step when using bun.

## Handle Results

### On Success

1. Create commit with version changes
2. Push branch to remote:
   ```bash
   git push -u origin "$BRANCH_NAME"
   ```
3. Check for existing dependency update PRs:
   ```bash
   gh pr list --search "chore: update dependencies" --state open
   ```
4. Create PR using gh CLI. Write the PR body to a temp file first (heredocs may fail in sandboxed environments):
   ```bash
   BODY_FILE=$(mktemp)
   cat > "$BODY_FILE" << 'PREOF'
   ## Summary
   - Updated packages: [list major version changes]
   - Breaking changes fixed: [list code modifications]

   ## Validation Results
   | Check | Status |
   |-------|--------|
   | Build | pass/fail |
   | Lint | pass/fail |
   | Tests | pass/fail |
   | Security Audit | X vulnerabilities |

   ## Files Changed
   - [list modified package.json files]

   Generated with [Claude Code](https://claude.com/claude-code)
   PREOF
   gh pr create --title "chore: update dependencies" --body-file "$BODY_FILE"
   rm -f "$BODY_FILE"
   ```
5. Return the PR URL to the user

### On Failure

- Categorize errors (build/lint/test/audit)
- Provide specific remediation steps
- Offer options: isolate problem, revert specific updates, or abandon
- If partially successful, still create PR with failing checks noted

## Error Categories

| Category | Examples | Remediation |
|----------|----------|-------------|
| Build | Type errors, missing dependencies | Update @types/*, check changelogs |
| Lint | Code style issues | Run `$PM run lint -- --fix` |
| Test | Breaking API changes | Review migration guides |
| Audit | Vulnerabilities | Manual remediation steps |

