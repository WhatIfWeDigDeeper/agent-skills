# Interactive Help

> **Note:** If package arguments were provided (e.g. `/uv-deps fastapi asyncpg`), they are already set. The workflow will target only those packages.

Display the following help summary to the user, then present the questions below using `AskUserQuestion`. The second question depends on the answer to the first, and the third depends on the answer to the second.

---

**uv-deps** — Maintain Python packages (uv-based projects) through security audits or dependency updates on a dedicated branch.

**Arguments:** Specific package names (e.g. `fastapi asyncpg`), `.` for all packages, or glob patterns (e.g. `django-*`).

**Workflows:**
- **Security audit** — Scan for CVEs, fix vulnerable packages, create PR with security report
- **Dependency updates** — Upgrade outdated packages with optional version and severity filters

---

## Question 1: Workflow type

Use `multiSelect: false`.

| Option | Description |
|--------|-------------|
| Update dependencies (Recommended) | Update Python packages to newer versions |
| Security fixes only | Only fix packages with known vulnerabilities |

## Question 2a: Version scope (if "Update dependencies" was selected)

Use `multiSelect: false`.

| Option | Description |
|--------|-------------|
| Patch + Minor (Recommended) | Include patch and minor version updates |
| Patch only | Include only patch-level updates (e.g. 2.1.3 to 2.1.4) |
| Patch + Minor + Major | Include all updates including major version upgrades |

## Question 3: Skip x.y.0 releases (shown after Q2a ONLY if "Patch + Minor" or "Patch + Minor + Major" was selected)

Omit this question entirely if "Patch only" was chosen — x.y.0 is a minor bump, not a patch, so the filter does not apply.

Use `multiSelect: false`.

| Option | Description |
|--------|-------------|
| Yes, skip x.y.0 — wait for x.y.1+ bug fixes (Recommended) | Skip x.y.0 releases and wait for the first bug-fix release |
| No, include x.y.0 releases | Include x.y.0 releases as soon as they are available |

## Question 2b: Severity scope (if "Security fixes only" was selected)

Use `multiSelect: false`.

| Option | Description |
|--------|-------------|
| Critical + High (Recommended) | Fix critical and high severity vulnerabilities |
| Critical only | Only fix critical severity vulnerabilities |
| Critical + High + Moderate | Include moderate severity vulnerabilities |
| All: Critical + High + Moderate + Low | Fix all vulnerabilities regardless of severity |

## After Selection

If no package arguments were provided, treat the package scope as `.` (all packages) when executing the selected workflow.

**Version scope mapping (Q2a answer → filter behavior):**
- "Patch only" — include packages where only the patch version differs (major and minor are the same)
- "Patch + Minor" — include packages where the patch or minor version differs (major is the same)
- "Patch + Minor + Major" — include all updates regardless of version component

**Skip x.y.0 mapping (Q3 answer → filter behavior):**
- "Yes, skip x.y.0" — if the latest version has patch=0 and minor>0 (e.g. `2.1.0`), exclude it from updates; does not apply to x.0.0 major releases
- "No, include x.y.0 releases" — no additional filtering; all versions matching the Q2a scope are included
- (Question absent when "Patch only" was chosen — no x.y.0 filtering is performed)

**Severity scope mapping (Q2b answer → filter behavior):**
- "Critical + High" — filter audit results to critical and high severity only
- "Critical only" — filter audit results to critical severity only
- "Critical + High + Moderate" — filter audit results to critical, high, and moderate severity
- "All: Critical + High + Moderate + Low" — include all vulnerabilities regardless of severity

Proceed with the selected workflow.
