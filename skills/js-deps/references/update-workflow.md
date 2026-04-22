# Dependency Update Workflow

Use the detected `$PM` package manager for all commands. See [package-managers.md](package-managers.md) for command mappings.

## Prerequisites

Ensure dependencies are installed first (SKILL.md step 6) so that `$PM outdated` can accurately compare installed vs. registry versions.

## Version Checking and Updates

### Discover What Needs Updating

Run the outdated check to get a list of packages to update. See [package-managers.md](package-managers.md) for the correct command per package manager.

**Note for npm monorepos:** If the root `package.json` has a `workspaces` field, run `npm outdated --workspaces` from the root instead of checking member directories individually.

Filter the results based on any version preferences expressed by the user — whether from the interactive help flow or from inline request phrasing (e.g., "only patch updates", "skip major versions"). The filter definitions are in [interactive-help.md](interactive-help.md) under "Update dependencies path".

If no packages are outdated after filtering, report that all packages are up to date and exit — do not commit, push, or create a PR.

### Parallelize Across Directories

If multiple directories need updates, launch a separate Task subagent (general-purpose, background) per directory. Each subagent handles installs, version checks, and package updates for its directory only — **do not commit from subagents**. The main agent commits all changes after all subagents complete.

**Critical: always use `--prefix` instead of `cd`** — shell working directory does not persist between Bash tool calls in subagents. A `cd /path && npm install` that spans two calls will run npm in the wrong directory. Always pass an absolute path via the `--prefix` flag so no `cd` is needed:
```bash
# Safe — no cd required, directory is explicit
npm install --prefix "$WORKTREE_PATH/some-pkg" --save-exact some-package@1.2.3

# Unsafe — cd does not persist if split across Bash calls
cd "$WORKTREE_PATH/some-pkg"
npm install --save-exact some-package@1.2.3
```
When writing subagent prompts, instruct subagents to use `npm install --prefix <absolute-path>` for all install commands.

When consolidating results:
- Collect packages updated, versions changed, and validation results from each subagent
- Merge into a single report; if any subagent fails, still include partial results from others
- Document any packages that couldn't be updated in the PR description

### Check and Update Versions

Use the **View Package Info** table in [package-managers.md](package-managers.md) to check latest versions and dist-tags per manager. Prefer an LTS dist-tag when available (bun does not support dist-tags natively).

Use the install command from the **Install/Update** table in [package-managers.md](package-managers.md) — the command verb differs by manager (`npm install` vs `yarn/pnpm/bun add`).

### Run Security Audit

After updating, check for new vulnerabilities:
```bash
$PM audit
# Run auto-fix if available for the detected package manager:
if [ "$PM" = "npm" ]; then
  npm audit fix
elif [ "$PM" = "pnpm" ]; then
  pnpm audit --fix  # pnpm 8+ only; older pnpm requires manual fixes
fi
# yarn does not support audit fix; bun does not support audit
```

For yarn: `audit fix` is not available — fix remaining vulnerabilities manually using the steps in [audit-workflow.md](audit-workflow.md). Note: bun does not support audit at all; skip this step when using bun.

## Handle Results

### On Success

1. Commit changes. Choose the message based on what was updated:
   - Patch/minor only: `"chore: update dependencies"`
   - Major bumps included: `"chore: update dependencies (major: pkg1 vX->Y, pkg2 vX->Y)"`
   ```bash
   git -C "$WORKTREE_PATH" add -A
   git -C "$WORKTREE_PATH" commit -m "<message from above>"
   # If commit fails due to GPG signing, retry with --no-gpg-sign
   ```
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
   # Use the same title as the commit message chosen above
   gh pr create --title "<commit message from step 1>" --body-file "$BODY_FILE"
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
| Build scripts | Type errors, missing dependencies | Update @types/*, check changelogs |
| Lint scripts | Code style issues | Run `$PM run <lint-script> -- --fix` |
| Test scripts | Breaking API changes | Review migration guides |
| Audit | Vulnerabilities | Manual remediation steps |

