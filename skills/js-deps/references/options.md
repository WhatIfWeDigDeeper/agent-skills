# Help Options

Read the skill's SKILL.md file and display its content as formatted documentation (title, arguments, workflows, process steps, and notes). Then present the questions below using `AskUserQuestion`. The second question depends on the answer to the first.

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
- **Skip .0 patches**: If the latest version ends in `.0` (e.g. `2.1.0`), skip it and keep the current version.

**Security fixes path:**
- Run `$PM audit` to identify vulnerable packages.
- Filter audit results by the selected severity levels before applying fixes.
- Use `$PM audit fix` (npm) or manually update vulnerable packages to patched versions.
