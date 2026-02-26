# Dependency Update Workflow

Use the detected `$PM` package manager for all commands. See [package-managers.md](package-managers.md) for command mappings.

## Prerequisites

Ensure dependencies are installed first (SKILL.md step 5) so that `$PM outdated` can accurately compare installed vs. registry versions.

## Version Checking and Updates

### Discover What Needs Updating

Run the outdated check to get a list of packages to update. See [package-managers.md](package-managers.md) for the correct command per package manager.

Filter the results based on any version preferences expressed by the user — whether from the interactive help flow or from inline request phrasing (e.g., "only patch updates", "skip major versions").

### Check and Update Versions

Use the appropriate commands for your package manager (see [package-managers.md](package-managers.md)):

```bash
# Check latest version — command differs by package manager (see package-managers.md View table)
npm view <package> version           # npm
yarn info <package> version          # yarn 1.x (use 'yarn info <pkg> --json' for yarn 2+)
pnpm view <package> version          # pnpm
bunx npm-view <package> version      # bun

# Prefer LTS when available (dist-tags not supported by bun natively)
npm view <package> dist-tags         # npm
yarn info <package> dist-tags        # yarn 1.x
pnpm view <package> dist-tags        # pnpm
```

Use the install command from the **Install/Update** table in [package-managers.md](package-managers.md) — the command verb differs by manager (`npm install` vs `yarn/pnpm/bun add`).

### Run Security Audit

After updating, check for new vulnerabilities:
```bash
$PM audit
npm audit fix  # npm only — do not run for yarn, pnpm, or bun
```

For yarn and pnpm: `audit fix` is not available — fix remaining vulnerabilities manually using the steps in [audit-workflow.md](audit-workflow.md). Note: bun does not support audit at all; skip this step when using bun.

## Handle Results

### On Success

1. Create commit with version changes
2. Push branch to remote:
   ```bash
   git push -u origin "$BRANCH_NAME"
   ```
3. Create PR using gh CLI. Write the PR body to a temp file first (heredocs may fail in sandboxed environments):
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
4. Return the PR URL to the user

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

