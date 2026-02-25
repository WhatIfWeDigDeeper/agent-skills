---
name: js-deps
description: Maintain JavaScript/Node.js packages through security audits or dependency updates using an isolated git worktree. Supports npm, yarn, pnpm, and bun. Use for security audits, CVE fixes, vulnerability checks, dependency updates, package upgrades, outdated packages, bump versions, fix npm vulnerabilities, modernize node_modules, or when user types "/js-deps" with or without specific package names or glob patterns.
license: MIT
compatibility: Requires git, a JavaScript package manager (npm, yarn, pnpm, or bun), and network access to package registries
metadata:
  author: Gregory Murray
  repository: github.com/whatifwedigdeeper/agent-skills
  version: "0.5"
---

# JS Deps

## Arguments

Specific package names (e.g. `jest @types/jest`), `.` for all packages, or glob patterns (e.g. `@testing-library/*`).

If `$ARGUMENTS` is `help`, `--help`, `-h`, or `?`, skip the workflow and read [references/options.md](references/options.md).

## Workflow Selection

Based on user request:
- **Security audit** (audit, CVE, vulnerabilities, security): Read [references/audit-workflow.md](references/audit-workflow.md)
- **Dependency updates** (update, upgrade, latest, modernize): Read [references/update-workflow.md](references/update-workflow.md)

If the user expresses version preferences (e.g., "only minor and patch", "skip major versions", "only critical CVEs"), apply the filters defined in [references/options.md](references/options.md) without requiring an explicit `--help` invocation.

## Shared Process

### 1. Create Worktree

Create an isolated git worktree so the main working directory is never modified:
```bash
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
BRANCH_NAME="js-deps-$TIMESTAMP"
WORKTREE_PATH="${TMPDIR:-/tmp}/$BRANCH_NAME"
git worktree add "$WORKTREE_PATH" -b "$BRANCH_NAME"
```

If `git worktree add` fails (e.g., sandbox permission error), prompt the user:
> `git worktree` requires write access to `$TMPDIR`. Choose an option:
> 1. Add `$TMPDIR` to your sandbox allowlist in `settings.json` (recommended)
> 2. Fall back to branch+stash approach

**All subsequent steps operate within `$WORKTREE_PATH`.** Discovery, installs, edits, and commits all happen there. Paths like `cd <directory>` in reference files are relative to `$WORKTREE_PATH`.

`gh`, `git push`, and `git commit` require `dangerouslyDisableSandbox: true` (keyring access for auth).

### 2. Detect Package Manager

Detect from lock files and `package.json` `packageManager` field (which takes precedence). See [references/package-managers.md](references/package-managers.md) for detection logic and command mappings.

### 3. Verify Registry Access

Verify the package manager CLI is available and, for npm, that it can reach the registry. See [references/package-managers.md](references/package-managers.md) for manager-specific verification commands.

If verification fails, prompt user: "Cannot reach package registry. Sandbox may be blocking network access. To allow package manager commands in sandbox mode, update settings.json."

Do not proceed until verification passes.

### 4. Discover Package Locations

Find all `package.json` files within `$WORKTREE_PATH` excluding `node_modules`. Store results as an array of directories to process.

### 5. Install Dependencies

**Skip this step for security audit workflows** — `$PM audit` reads from lock files and does not require `node_modules`.

For dependency update workflows only: install dependencies so that `$PM outdated` can accurately compare installed vs. registry versions. Without `node_modules`, exact-pinned packages (no `^` or `~`) won't appear in outdated reports. If `$ARGUMENTS` specifies particular packages (not `.`), only install in directories where those packages appear in `package.json`.

### 6. Identify Packages

- Parse `$ARGUMENTS` to determine packages
- For globs, expand against package.json dependencies
- For `.`, process all packages

### 7. Validate Changes

Run validation **per directory** after each package update. Check `package.json` scripts and run available commands using `$PM run <script>` in order: build, lint, test. Skip any that don't exist.

- **Build failure** is a hard failure: revert the package before continuing.
- **Lint or test failure** is a soft failure: report it but continue with remaining packages.

Continue running all validators even on failure to collect the full error set before reporting.

If a build fails for a specific package, revert before continuing with remaining packages:
```bash
# Run from within $WORKTREE_PATH/<directory>
git checkout -- .  # revert all tracked changes in this directory (package.json + lock file)
$PM install
```

### 8. Update Documentation for Major Version Changes

For major version upgrades (e.g., 18.x to 19.x):

1. Search for version references in markdown files
2. Update in: `CLAUDE.md`, `README.md`, `docs/*.md`
3. Include changes in report/PR description

### 9. Cleanup

Remove the worktree. The main working directory was never modified, so no stash restore is needed.

```bash
git worktree remove "$WORKTREE_PATH" --force
# Only delete branch if no PR was created
if ! gh pr view "$BRANCH_NAME" --json url > /dev/null 2>&1; then
  git branch -d "$BRANCH_NAME"
fi
```

`--force` handles cases where the skill failed mid-run with uncommitted changes in the worktree.

## Edge Cases

- **Glob matches nothing**: Warn and list available packages
- **Unsupported package manager**: Prompt user for guidance
- **Peer dep conflicts after major upgrades**: When a plugin doesn't declare support for the new major version of its host (e.g., `eslint-plugin-react-hooks` not supporting eslint 10), add `"overrides"` to `package.json` rather than using `--legacy-peer-deps`. Example: `"overrides": { "eslint-plugin-react-hooks": { "eslint": "$eslint" } }`. The `$eslint` syntax references the version already declared in the package's own dependencies
- **Lockfile sync**: After all package.json changes, run `$PM install` in every modified directory and commit lockfiles — CI tools like `npm ci` require exact sync between package.json and the lockfile
- **Verify devDependencies placement**: After bulk installs across directories, verify that linting/testing/build packages (eslint, typescript, vite, etc.) ended up in `devDependencies`, not `dependencies` — easy to misplace when running install commands across many directories
