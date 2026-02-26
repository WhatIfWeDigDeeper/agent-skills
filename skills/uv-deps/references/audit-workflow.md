# Security Audit Workflow

Use `uv` and `uvx` for all commands. See [uv-commands.md](uv-commands.md) for command reference.

## Audit Execution

### Run Security Audit on Each Directory

For each directory containing pyproject.toml, use the `uv export` pipeline pattern (required for pip-audit compatibility across all Python versions — see [uv-commands.md](uv-commands.md)). Capture the output into a variable — do **not** echo raw JSON to the user.

`<directory>` is relative to `$WORKTREE_PATH` (use `"$WORKTREE_PATH"` directly for a root project).

```bash
cd "$WORKTREE_PATH/<directory>"
AUDIT_JSON=$(uv export --frozen | uvx pip-audit --strict --format json --desc -r /dev/stdin --disable-pip --no-deps 2>/dev/null)
AUDIT_EXIT=$?
# Extract only packages with vulnerabilities
VULN_JSON=$(echo "$AUDIT_JSON" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    vulns = [d for d in data['dependencies'] if d['vulns']]
    print(json.dumps(vulns, indent=2))
except (json.JSONDecodeError, KeyError) as e:
    print(f'Warning: failed to parse pip-audit output: {e}', file=sys.stderr)
    print('[]')
")
# If VULN_JSON is empty but AUDIT_EXIT indicates vulnerabilities, the JSON was malformed
if [ "$AUDIT_EXIT" -ne 0 ] && [ "$VULN_JSON" = "[]" ]; then
  echo "Warning: pip-audit reported vulnerabilities but output could not be parsed. Check raw output." >&2
fi
```

`uv export` includes hashes by default, which satisfies pip-audit's hash requirement. `2>/dev/null` drops remaining pip-audit progress noise. pip-audit exits 1 if vulnerabilities are found, 0 if the environment is clean. `uv export --frozen` requires a `uv.lock` to exist — this is ensured by running `uv sync` in SKILL.md step 4.

> **Note on `--strict`:** This flag causes pip-audit to exit non-zero on warnings (e.g., packages with no OSV/PyPI safety DB entry). If the audit exits non-zero but `VULN_JSON` parses as empty, the warning above will fire. As a fallback, retry without `--strict` to distinguish true vulnerabilities from database-coverage warnings.

Use `AUDIT_EXIT` to skip further processing when a directory is clean:
```bash
if [ "$AUDIT_EXIT" -eq 0 ]; then
  echo "No vulnerabilities in this directory."
  # continue to next directory
fi
```

Collect all audit results into a consolidated report. Present only the vulnerable packages — never dump the full dependency list or raw JSON to the user.

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
# Extract GHSA IDs from vulnerability JSON, look up severity for each
# Use a temp file — `| while read` runs in a subshell and cannot set parent variables
SEVERITY_MAP_FILE=$(mktemp)
echo "$VULN_JSON" | python3 -c "
import json, sys
data = json.load(sys.stdin)
for pkg in data:
    for vuln in pkg['vulns']:
        for alias in vuln.get('aliases', []):
            if alias.startswith('GHSA-'):
                print(alias)
" | while read GHSA_ID; do
  # Use jq's '//' operator to default null to "high" (handles rate-limit responses that return null)
  SEVERITY=$(gh api /advisories/$GHSA_ID --jq '.severity // "high"' 2>/dev/null || echo "high")
  # Normalize "low" to "moderate" to match the filter option labels
  # (GitHub Advisory API returns: low, moderate, high, critical — "medium" is not used)
  SEVERITY=$(echo "$SEVERITY" | sed -E 's/^low$/moderate/')
  echo "$GHSA_ID: $SEVERITY" >> "$SEVERITY_MAP_FILE"
done
SEVERITY_MAP=$(cat "$SEVERITY_MAP_FILE")
rm -f "$SEVERITY_MAP_FILE"
```

If no GHSA alias exists or the lookup fails, treat as "high" by default.

### Apply Severity Filter

If the user selected specific severity levels (not "All vulnerabilities"), build a map of vuln ID → severity from the GHSA lookups above, then filter `VULN_JSON`:

```bash
# SELECTED_SEVERITIES: space-separated lowercase severity names derived from the user's
# multiSelect answers in interactive-help.md (e.g. "critical high" or "moderate").
# Leave empty (unset) to include all severities — do not set it when "All vulnerabilities" is selected.
# Valid values match the normalized GitHub API severities: critical, high, moderate (includes low).
if [ -n "$SELECTED_SEVERITIES" ]; then
  VULN_JSON=$(echo "$VULN_JSON" | SELECTED_SEVERITIES="$SELECTED_SEVERITIES" SEVERITY_MAP="$SEVERITY_MAP" python3 -c "
import json, sys, os
selected = set(os.environ.get('SELECTED_SEVERITIES', '').lower().split())
# severity_map built from GHSA lookups: {'GHSA-xxxx-xxxx-xxxx': 'high', ...}
severity_map = {}
for line in os.environ.get('SEVERITY_MAP', '').strip().split('\n'):
    if ': ' in line:
        ghsa_id, sev = line.split(': ', 1)
        severity_map[ghsa_id.strip()] = sev.strip().lower()
data = json.load(sys.stdin)
def pkg_matches(pkg):
    for vuln in pkg['vulns']:
        for alias in vuln.get('aliases', []):
            if alias.startswith('GHSA-') and severity_map.get(alias, 'high') in selected:
                return True
    return False
print(json.dumps([p for p in data if pkg_matches(p)], indent=2))
")
fi
```

`SEVERITY_MAP` is built by the GHSA lookup above and is ready for use here.

Capture the original vulnerability count before making any fixes:
```bash
ORIGINAL_COUNT=$(echo "$VULN_JSON" | python3 -c "
import json, sys
data = json.load(sys.stdin)
print(sum(len(p['vulns']) for p in data))
")
```

### Determine Strategy

Always update packages **sequentially within a directory** to avoid lock file races.

Parallelize **across directories** only: if multiple directories have vulnerabilities, launch a separate Task subagent (general-purpose, background) per directory. Each subagent handles package updates and validation for its directory only — **do not commit from subagents**. The main agent commits all changes after all subagents complete. Include `ORIGINAL_COUNT`, `WORKTREE_PATH`, and `BRANCH_NAME` in each subagent's task prompt so it can run the post-audit scan and report progress.

When consolidating results:
- Collect vulnerability counts (before/after), packages fixed, and validation status from each subagent
- Merge into a single report; if any subagent fails, still include partial results for the others

### Update Packages

For each vulnerable package, pin to the fix version:
```bash
cd "$WORKTREE_PATH/<directory>"
uv add <package>==<fix_version>
uv sync  # add --extra dev or --group dev as appropriate — see uv-commands.md
```

If multiple fix versions are available, prefer the closest version to the current one that resolves the vulnerability.

Validate after each update per SKILL.md step 6. If validation fails, revert (see SKILL.md step 6) before continuing.

### Post-Audit Scan

Re-run the audit to confirm fixes:
```bash
cd "$WORKTREE_PATH/<directory>"
# REAUDIT_JSON is raw pip-audit output (a dict with a 'dependencies' key),
# unlike VULN_JSON above which is a pre-filtered list of dicts.
REAUDIT_JSON=$(uv export --frozen | uvx pip-audit --strict --format json --desc -r /dev/stdin --disable-pip --no-deps 2>/dev/null)
REAUDIT_EXIT=$?
REMAINING=$(echo "$REAUDIT_JSON" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    remaining = sum(len(d['vulns']) for d in data['dependencies'])
    print(remaining)
except (json.JSONDecodeError, KeyError):
    print('unknown')
")
if [ "$REMAINING" = "unknown" ]; then
  echo "Warning: re-audit output could not be parsed — fix status unknown" >&2
else
  echo "Fixed $((ORIGINAL_COUNT - REMAINING)) of $ORIGINAL_COUNT vulnerabilities ($REMAINING remaining)"
fi
```

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
