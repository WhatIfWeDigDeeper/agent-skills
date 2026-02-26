# Help Options

Display the following help summary to the user, then present the questions below using `AskUserQuestion`. The second question depends on the answer to the first.

---

**js-deps** — Maintain JavaScript/Node.js packages through security audits or dependency updates using an isolated git worktree. Supports npm, yarn, pnpm, and bun.

**Arguments:** Specific package names (e.g. `jest @types/jest`), `.` for all packages, or glob patterns (e.g. `@testing-library/*`).

**Workflows:**
- **Security audit** — Scan for CVEs, fix vulnerable packages, create PR with security report
- **Dependency updates** — Upgrade outdated packages with optional version and severity filters

---

## Question 1: Workflow type

Use `multiSelect: false`.

| Option | Description |
|--------|-------------|
| Update dependencies | Update packages to newer versions |
| Security fixes only | Only fix packages with known vulnerabilities |

## Question 2a: Update filters (if "Update dependencies" was selected)

Use `multiSelect: true`. Only selected version types are included in the update.

| Option | Description |
|--------|-------------|
| Major | Include major version upgrades (e.g. 2.x → 3.x) |
| Minor | Include minor version updates (e.g. 2.1 → 2.2) |
| Patch | Include patch-level updates (e.g. 2.1.3 → 2.1.4) |
| Skip .0 patches (Recommended) | Skip x.y.0 releases and wait for x.y.1+ bugfix releases |

## Question 2b: Severity filter (if "Security fixes only" was selected)

Use `multiSelect: true`. Nothing selected by default means all severities are included.

| Option | Description |
|--------|-------------|
| Critical | Only fix critical severity vulnerabilities |
| High | Include high severity vulnerabilities |
| Moderate | Include moderate severity vulnerabilities |
| All vulnerabilities (Recommended) | Fix all reported vulnerabilities regardless of severity |

## How to Apply

**Update dependencies path:**
- **Major selected**: Include packages where the new major version differs from the current major version.
- **Minor selected**: Include packages where the new minor version differs (but major is the same).
- **Patch selected**: Include packages where only the patch version differs.
- **None selected**: If no version types are selected, default to including all (major, minor, and patch).
- **Skip .0 patches**: A modifier applied on top of the selected version filters. If the latest version has patch=0 and minor>0 (e.g. `2.1.0`), skip it — wait for `x.y.1+`. Do **not** apply this filter to `x.0.0` releases (e.g. `3.0.0`) — those are governed by the Major filter. This modifier only activates when a Patch-type update would otherwise be applied.

**Security fixes path:**
- Run `$PM audit` to identify vulnerable packages.
- Filter audit results by the selected severity levels before applying fixes.
- Use the audit fix commands from [package-managers.md](package-managers.md). For npm, `npm audit fix` can auto-remediate. For yarn and pnpm, fix manually. Bun does not support audit.
