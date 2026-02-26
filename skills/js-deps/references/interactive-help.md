# Interactive Help

> **Note:** If package arguments were provided (e.g. `/js-deps react lodash`), they are already set. The workflow will target only those packages.

Display the following help summary to the user, then present the questions below using `AskUserQuestion`. The second question depends on the answer to the first, and the third depends on the answer to the second.

---

**js-deps** — Maintain JavaScript/Node.js packages (npm/yarn/pnpm/bun projects) through security audits or dependency updates on a dedicated branch.

**Arguments:** Specific package names (e.g. `jest @types/jest`), `.` for all packages, or glob patterns (e.g. `@testing-library/*`).

**Workflows:**
- **Security audit** — Scan for CVEs, fix vulnerable packages, create PR with security report
- **Dependency updates** — Upgrade outdated packages with optional version and severity filters

---

## Question 1: Workflow type

Use `multiSelect: false`.

| Option | Description |
|--------|-------------|
| Update dependencies (Recommended) | Update packages to newer versions |
| Security fixes only | Only fix packages with known vulnerabilities |

## Question 2a: Version scope (if "Update dependencies" was selected)

Use `multiSelect: false`.

| Option | Description |
|--------|-------------|
| Patch + Minor (Recommended) | Include patch and minor version updates |
| Patch only | Include only patch-level updates (e.g. 2.1.3 to 2.1.4) |
| Patch + Minor + Major | Include all updates including major version upgrades |

## Question 3: Skip x.y.0 releases (if "Patch + Minor" or "Patch + Minor + Major" was selected)

Use `multiSelect: false`. Only shown when minor updates are in scope — omit entirely if "Patch only" was chosen, since x.y.0 is a minor bump, not a patch.

| Option | Description |
|--------|-------------|
| Yes, skip x.y.0 — wait for x.y.1+ bug fixes (Recommended) | Skip x.y.0 releases and wait for x.y.1+ bugfix releases |
| No, include x.y.0 releases | Include all minor releases including x.y.0 |

## Question 2b: Severity scope (if "Security fixes only" was selected)

Use `multiSelect: false`.

| Option | Description |
|--------|-------------|
| Critical + High (Recommended) | Fix critical and high severity vulnerabilities |
| Critical only | Only fix critical severity vulnerabilities |
| Critical + High + Moderate | Include moderate severity vulnerabilities |
| All: Critical + High + Moderate + Low | Fix all vulnerabilities regardless of severity |

## After Selection

The selected answers map to filter behavior as follows:

**Update dependencies path:**
- **Patch only**: include packages where only the patch version differs (major and minor are the same).
- **Patch + Minor** (default): include packages where the patch or minor version differs (major is the same).
- **Patch + Minor + Major**: include all packages with any version difference.
- **Skip x.y.0**: if the latest version has patch=0 and minor>0 (e.g. `2.1.0`), skip it — wait for `x.y.1+`. Does not apply to `x.0.0` major releases.

**Security fixes path:**
- Run `$PM audit` to identify vulnerable packages.
- Apply a severity filter based on the selected option from Question 2b:
  - **Critical + High (Recommended)**: include only Critical and High vulnerabilities.
  - **Critical only**: include only Critical vulnerabilities.
  - **Critical + High + Moderate**: include Critical, High, and Moderate vulnerabilities; exclude Low.
  - **All: Critical + High + Moderate + Low**: include all vulnerabilities regardless of severity.

If no package arguments were provided, treat the package scope as `.` (all packages) when executing the selected workflow. Proceed with the workflow.
