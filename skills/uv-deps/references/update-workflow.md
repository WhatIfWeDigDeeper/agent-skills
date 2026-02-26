# Dependency Update Workflow

Use `uv` for all commands. See [uv-commands.md](uv-commands.md) for command reference.

## Version Checking and Updates

### Check Outdated Packages

```bash
cd "$WORKTREE_PATH/<directory>"
uv pip list --outdated
```

> **Prerequisite:** `uv sync` must have run first (SKILL.md step 4) so the environment is populated and `uv pip list --outdated` can compare installed vs. PyPI versions.

> **Note:** `uv pip list --outdated` compares installed versions to PyPI latest and does not account for version range constraints in `pyproject.toml`. A package may appear outdated but be unupgradable given its constraints — the update step handles this.

For specific packages, check available versions:
```bash
uv index versions <package>
```

### Apply Version Filters

Compare each outdated package's current and latest versions to determine its update type, then include only packages matching the selected filters:

- **Major selected**: Include packages where the new major version differs from the current.
- **Minor selected**: Include packages where the new minor version differs (major is the same).
- **Patch selected**: Include packages where only the patch version differs.
- **None selected**: Default to including all (major, minor, and patch).
- **Skip x.y.0 releases**: If the latest version has patch=0 **and minor>0** (e.g. `2.1.0`), skip it — wait for `x.y.1+`. Do **not** apply this filter to `x.0.0` major releases (e.g. `3.0.0`) — those are governed by the Major filter.

  Implementation check:
  ```python
  # latest_version is a tuple (major, minor, patch)
  should_skip = (
      skip_x_y_0_selected
      and latest_version[2] == 0   # patch is 0
      and latest_version[1] > 0    # minor > 0 (not a major release)
  )
  ```

### Determine Strategy

Per directory:
- **1-3 packages**: Update sequentially
- **4+ packages**: Use parallel Task subagents (2 packages per agent)

If multiple directories have outdated packages, process them in parallel using separate Task subagents (general-purpose), running in background. Collect results from all agents before generating the final report.

### Update Packages

Update both pyproject.toml and the lockfile. First, check the project's existing version specifier style in `pyproject.toml`:

- **Exact pins** (`==1.2.3`): Use `uv add <pkg>==<latest_version>`
- **Range constraints** (`>=1.2,<2.0` or `~=1.2`): Edit `pyproject.toml` using file editing tools to update the range bounds, then run `uv lock --upgrade-package <pkg>` and `uv sync`
- **Unpinned** (`requests` with no specifier): Use `uv add <pkg>` (no version) to pull latest and let uv resolve

```bash
cd "$WORKTREE_PATH/<directory>"

# Check latest version
uv index versions <package>

# For exact-pinned projects:
uv add <package>==<latest_version>

# For range-constrained projects:
# Edit pyproject.toml manually, then:
uv lock --upgrade-package <package>
uv sync

# For dev dependencies — check pyproject.toml to pick the right flag:
#   [project.optional-dependencies] → uv add --optional dev <pkg>==<version>
#   [dependency-groups] (PEP 735)   → uv add --group dev <pkg>==<version>

# Sync environment (match the pattern above):
#   [project.optional-dependencies] → uv sync --extra dev
#   [dependency-groups] (PEP 735)   → uv sync --group dev
```

If `uv add <pkg>==<latest_version>` fails due to version constraints, try letting uv resolve the best compatible version:
```bash
uv add <package>  # no version pin — uv picks latest compatible with existing constraints
```
If that also fails, document the constraint conflict in the PR description and skip this package.

Validate after each update per SKILL.md step 6. If validation fails, revert (see SKILL.md step 6) before continuing.

### Update Documentation for Major Version Changes

For major version upgrades, search markdown files (`CLAUDE.md`, `README.md`, `docs/*.md`) for version references and update them. Include changes in the PR description.

### Workspace Projects

For uv workspaces (`[tool.uv.workspace]` in root `pyproject.toml`), run all `uv add`, `uv lock`, and `uv sync` commands from the workspace root. Member `pyproject.toml` files may still need direct edits for range constraints.

### Run Security Audit

After updating, check for new vulnerabilities (see [uv-commands.md](uv-commands.md) for details on this pattern):
```bash
cd "$WORKTREE_PATH/<directory>"
AUDIT_JSON=$(uv export --frozen | uvx pip-audit --strict --format json --desc -r /dev/stdin --disable-pip --no-deps 2>/dev/null)
AUDIT_EXIT=$?
VULN_COUNT=$(echo "$AUDIT_JSON" | python3 -c "import json,sys; data=json.load(sys.stdin); print(sum(len(d['vulns']) for d in data['dependencies']))" 2>/dev/null || echo "unknown")
```

Report a clean/vulnerable summary (e.g. "0 vulnerabilities" or "2 vulnerabilities found") — do not print raw JSON.

## Handle Results

### On Success

1. Commit changes per SKILL.md step 7
2. Push branch to remote:
   ```bash
   git push -u origin "$BRANCH_NAME"
   ```
3. Check for existing dependency update PRs:
   ```bash
   gh pr list --search "chore: update Python dependencies" --state open
   ```
   If an open PR exists for this branch (`$BRANCH_NAME`), update it with `gh pr edit` instead of creating a new one. If it's on a different branch, create a new PR as usual.
4. Create PR using gh CLI. Write the PR body to a temp file first (subshell heredocs `$(cat <<'EOF'...)` fail in sandbox):
   ```bash
   BODY_FILE=$(mktemp)
   cat > "$BODY_FILE" << 'PREOF'
   ## Summary
   - Updated packages: [list with old → new versions]
   - Breaking changes fixed: [list code modifications if any]

   ## Validation Results
   | Check | Status |
   |-------|--------|
   | Type Check (mypy) | pass/fail |
   | Lint (ruff) | pass/fail |
   | Tests (pytest) | pass/fail |
   | Security Audit (pip-audit) | clean/X vulnerabilities |

   ## Files Changed
   - [list modified pyproject.toml and uv.lock files]

   Generated with [Claude Code](https://claude.com/claude-code)
   PREOF
   gh pr create --title "chore: update Python dependencies" --body-file "$BODY_FILE"
   rm -f "$BODY_FILE"
   ```
5. Return the PR URL to the user

### On Failure

- Categorize errors (type check/lint/test/audit)
- Provide specific remediation steps
- Offer options: isolate problem, revert specific updates, or abandon
- If partially successful, still create PR with failing checks noted
