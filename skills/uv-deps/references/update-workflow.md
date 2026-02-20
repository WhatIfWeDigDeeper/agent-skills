# Dependency Update Workflow

Use `uv` for all commands. See [uv-commands.md](uv-commands.md) for command reference.

## Version Checking and Updates

### Check Outdated Packages

```bash
cd <directory>
uv pip list --outdated
```

> **Note:** `uv pip list --outdated` compares installed versions to PyPI latest and does not account for version range constraints in `pyproject.toml`. A package may appear outdated but be unupgradable given its constraints — the update step handles this.

For specific packages, check available versions:
```bash
uv pip index versions <package>
```

### Apply Version Filters

Compare each outdated package's current and latest versions to determine its update type, then include only packages matching the selected filters:

- **Major selected**: Include packages where the new major version differs from the current.
- **Minor selected**: Include packages where the new minor version differs (major is the same).
- **Patch selected**: Include packages where only the patch version differs.
- **None selected**: Default to including all (major, minor, and patch).
- **Skip x.y.0 releases**: If the latest version has patch=0 (e.g. `2.1.0`, `3.0.0`), skip it and keep the current version — wait for the first bugfix release (x.y.1+).

### Determine Strategy

Per directory:
- **1-3 packages**: Update sequentially
- **4+ packages**: Use parallel Task subagents (2 packages per agent)

If multiple directories have outdated packages, process them in parallel using separate Task subagents (general-purpose), running in background. Collect results from all agents before generating the final report.

### Update Packages

Update both pyproject.toml and the lockfile. First, check the project's existing version specifier style in `pyproject.toml`:

- **Exact pins** (`==1.2.3`): Use `uv add <pkg>==<latest_version>`
- **Range constraints** (`>=1.2,<2.0` or `~=1.2`): Edit `pyproject.toml` manually to update the range bounds, then run `uv lock --upgrade-package <pkg>` and `uv sync`
- **Unpinned** (`requests` with no specifier): Use `uv add <pkg>` (no version) to pull latest and let uv resolve

```bash
cd <directory>

# Check latest version
uv pip index versions <package>

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

Validate after each update per SKILL.md step 6. If validation fails, revert (see SKILL.md step 6) before continuing.

### Update Documentation for Major Version Changes

For major version upgrades, search markdown files (`CLAUDE.md`, `README.md`, `docs/*.md`) for version references and update them. Include changes in the PR description.

### Workspace Projects

For uv workspaces (`[tool.uv.workspace]` in root `pyproject.toml`), run all `uv add`, `uv lock`, and `uv sync` commands from the workspace root. Member `pyproject.toml` files may still need direct edits for range constraints.

### Run Security Audit

After updating, check for new vulnerabilities (see [uv-commands.md](uv-commands.md) for details on this pattern):
```bash
cd <directory>
uv export --frozen | uvx pip-audit --strict --format json --desc -r /dev/stdin --disable-pip --no-deps
```

## Handle Results

### On Success

1. Commit changes per SKILL.md step 7
2. Push branch to remote:
   ```bash
   git push -u origin "$BRANCH_NAME"
   ```
3. Check for existing dependency update PRs:
   ```bash
   gh pr list --search "chore: Update Python dependencies" --state open
   ```
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
   gh pr create --title "chore: Update Python dependencies" --body-file "$BODY_FILE"
   rm -f "$BODY_FILE"
   ```
5. Return the PR URL to the user

### On Failure

- Categorize errors (type check/lint/test/audit)
- Provide specific remediation steps
- Offer options: isolate problem, revert specific updates, or abandon
- If partially successful, still create PR with failing checks noted
