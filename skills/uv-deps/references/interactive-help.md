# Interactive Help

> **Note:** If package arguments were provided (e.g. `/uv-deps fastapi asyncpg`), they are already set. The workflow will target only those packages.

Display the following help summary to the user, then present the questions below using `AskUserQuestion`. The second question depends on the answer to the first.

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
| Update dependencies | Update Python packages to newer versions |
| Security fixes only | Only fix packages with known vulnerabilities |

## Question 2a: Update filters (if "Update dependencies" was selected)

Use `multiSelect: true`. Only selected version types are included in the update. If no version types are selected (Major/Minor/Patch all unselected), all version types will be included by default.

| Option | Description |
|--------|-------------|
| Major | Include major version upgrades (e.g. 2.x to 3.x) |
| Minor | Include minor version updates (e.g. 2.1 to 2.2) |
| Patch | Include patch-level updates (e.g. 2.1.3 to 2.1.4) |
| Skip x.y.0 releases (Recommended) | Skip x.y.0 releases, wait for x.y.1+ bugfix releases |

## Question 2b: Severity filter (if "Security fixes only" was selected)

Use `multiSelect: true`. Select one or more severity levels to filter. Leave all unselected to include all severities.

| Option | Description |
|--------|-------------|
| All vulnerabilities (Recommended) | Fix all reported vulnerabilities regardless of severity |
| Critical | Only fix critical severity vulnerabilities |
| High | Include high severity vulnerabilities |
| Moderate | Include moderate/low severity vulnerabilities |

**Resolution rule:** If "All vulnerabilities" is selected, ignore any other severity selections and treat all severities as in scope.

## After Selection

If no package arguments were provided, treat the package scope as `.` (all packages) when executing the selected workflow. Proceed with the workflow.
