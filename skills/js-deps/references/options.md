# Help Options

Display the skill's `description` from frontmatter as a one-line summary, then present two questions using `AskUserQuestion`. After the user selects options, store their choices and restart the workflow with those constraints applied.

## Question 1: Update scope

Use `multiSelect: false`. These options are mutually exclusive.

| Option | Description |
|--------|-------------|
| All versions (default) | Apply major, minor, and patch updates |
| Minor and patch only | Skip major version upgrades, only apply minor and patch updates |
| Patch only | Only apply patch-level updates (e.g. 1.2.3 → 1.2.4) |

## Question 2: Additional filters

Use `multiSelect: true`. These can be combined.

| Option | Description |
|--------|-------------|
| Skip .0 patches | Skip x.y.0 releases and wait for x.y.1+ bugfix releases |
| Security fixes only | Only update packages that have known vulnerabilities |
| Dry run | Show what would be updated without making any changes |

## How to Apply

When options are selected, apply them as filters during the update workflow:
- **Minor and patch only**: When checking outdated packages, skip any where the new major version differs from the current major version.
- **Patch only**: Skip any package where the minor or major version differs.
- **Skip .0 patches**: If the latest version ends in `.0` (e.g. `2.1.0`), skip it and keep the current version.
- **Security fixes only**: Cross-reference outdated packages with `$PM audit` output. Only update packages that appear in the audit report.
- **Dry run**: Run the full discovery and version-check steps, display a summary table of what would change, then stop without modifying any files or creating a branch.
