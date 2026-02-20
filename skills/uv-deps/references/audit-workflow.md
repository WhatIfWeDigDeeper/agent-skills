# Security Audit Workflow

Use `uv` and `uvx` for all commands. See [uv-commands.md](uv-commands.md) for command reference.

## Audit Execution

### Run Security Audit on Each Directory

For each directory containing pyproject.toml, use the `uv export` pipeline pattern (required for Python 3.14 compatibility — see [uv-commands.md](uv-commands.md)):
```bash
cd <directory>
uv export --frozen | uvx pip-audit --strict --format json --desc -r /dev/stdin --disable-pip --no-deps
```

Parse the JSON output directly from stdout. Collect all audit results into a consolidated report.

### Categorize by Severity

Parse the JSON output. Each dependency entry contains a `vulns` array with vulnerability details:
```json
{
  "dependencies": [
    {
      "name": "package-name",
      "version": "1.0.0",
      "vulns": [
        {
          "id": "PYSEC-2024-XXX",
          "fix_versions": ["1.0.1"],
          "aliases": ["CVE-2024-XXXXX", "GHSA-xxxx-xxxx-xxxx"],
          "description": "..."
        }
      ]
    }
  ]
}
```

Map to severity by looking up the GHSA alias from each vulnerability entry. Collect all GHSA IDs first, then look them up before making any file changes (to avoid interleaving API calls with edits):

```bash
for GHSA_ID in <ghsa-id-1> <ghsa-id-2> ...; do
  gh api /advisories/$GHSA_ID --jq '{id:.ghsa_id,severity:.severity}'
done
```

If no GHSA alias exists or the lookup fails, treat as "High" by default.

### Apply Severity Filter

Filter audit results by the selected severity levels before applying fixes. If no severity filter was selected, include all severities.

### Determine Strategy

Per directory:
- **1-3 packages**: Update sequentially
- **4+ packages**: Use parallel Task subagents (2 packages per agent)

If multiple directories have vulnerabilities, process them in parallel using separate Task subagents (general-purpose), running in background. Collect results from all agents before generating the final report.

### Update Packages

For each vulnerable package, pin to the fix version:
```bash
cd <directory>
uv add <package>==<fix_version>
uv sync  # add --extra dev or --group dev as appropriate — see uv-commands.md
```

If multiple fix versions are available, prefer the closest version to the current one that resolves the vulnerability.

Validate after each update per SKILL.md step 6. If validation fails, revert (see SKILL.md step 6) before continuing.

### Post-Audit Scan

Re-run the audit to confirm fixes:
```bash
cd <directory>
uv export --frozen | uvx pip-audit --strict --format json --desc -r /dev/stdin --disable-pip --no-deps
```

Compare before/after JSON output to confirm vulnerability counts decreased.

## Handle Results

### On Success

1. Generate consolidated security report
2. Commit changes per SKILL.md step 7
3. Push branch to remote:
   ```bash
   git push -u origin "$BRANCH_NAME"
   ```
4. Create PR using gh CLI. Write the PR body to a temp file first (subshell heredocs `$(cat <<'EOF'...)` fail in sandbox):
   ```bash
   BODY_FILE=$(mktemp)
   cat > "$BODY_FILE" << 'PREOF'
   ## Summary
   - Vulnerabilities fixed: [count]
   - Remaining vulnerabilities: [count with reasons]

   ## Changes
   [list packages updated with old → new versions]

   ## Validation Results
   | Check | Status |
   |-------|--------|
   | Type Check (mypy) | pass/fail |
   | Lint (ruff) | pass/fail |
   | Tests (pytest) | pass/fail |
   | Security Audit (pip-audit) | X remaining |

   Generated with [Claude Code](https://claude.com/claude-code)
   PREOF
   gh pr create --title "fix: patch vulnerable Python dependencies" --body-file "$BODY_FILE"
   rm -f "$BODY_FILE"
   ```
5. Return the PR URL to the user

### On Failure

- Categorize by directory and package
- Provide specific remediation steps for unfixable vulnerabilities
- If partially successful, still create PR with remaining issues noted

### Upstream-Unfixable Vulnerabilities

When no fix version is available for a vulnerability:

1. Document the vulnerability ID and affected package in the PR description
2. Add `--ignore-vuln <ID>` to the project's pip-audit CI command (e.g., in `Makefile`, CI config, or `pyproject.toml` scripts) if it blocks CI
3. Explain why no fix is available (e.g., upstream hasn't released a patch)
4. Include the ignore flag change in the same commit/PR as the fixable updates
