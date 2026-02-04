# Dependency Update Workflow

## Version Checking and Updates

### Check and Update Versions

```bash
# Check latest version
npm view <package> version

# Prefer LTS when available
npm view <package> dist-tags

# Update packages
npm install <package>@latest
```

### Run Security Audit

After updating, check for new vulnerabilities:
```bash
npm audit
npm audit fix
```

## Handle Results

### On Success

1. Create commit with version changes
2. Push branch to remote:
   ```bash
   git push -u origin "$BRANCH_NAME"
   ```
3. Check for existing dependency update PRs:
   ```bash
   gh pr list --search "chore: Update npm dependencies" --state open
   ```
4. Create PR using gh CLI:
   ```bash
   gh pr create --title "chore: Update npm dependencies" --body "$(cat <<'EOF'
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
   EOF
   )"
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
| Lint | Code style issues | Run `npm run lint -- --fix` |
| Test | Breaking API changes | Review migration guides |
| Audit | Vulnerabilities | Manual remediation steps |

## Cleanup Note

After creating a PR, do not delete the branch - it's needed for the open PR.
