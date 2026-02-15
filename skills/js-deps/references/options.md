# Help Options

Display the skill's `description` from frontmatter as a one-line summary, then present two questions using `AskUserQuestion`. After the user selects options, store their choices and restart the workflow with those constraints applied.

## Question 1: Version types to include

Use `multiSelect: true`. All are selected by default — users deselect what they want to skip.

| Option | Description |
|--------|-------------|
| Major (Recommended) | Include major version upgrades (e.g. 2.x → 3.x) |
| Minor (Recommended) | Include minor version updates (e.g. 2.1 → 2.2) |
| Patch (Recommended) | Include patch-level updates (e.g. 2.1.3 → 2.1.4) |

## Question 2: Additional filters

Use `multiSelect: true`. These can be combined.

| Option | Description |
|--------|-------------|
| Skip .0 patches (Recommended) | Skip x.y.0 releases and wait for x.y.1+ bugfix releases |
| Security fixes only | Only update packages that have known vulnerabilities |
| Dry run | Show what would be updated without making any changes |

## How to Apply

When options are selected, apply them as filters during the update workflow:
- **Major not selected**: Skip any package where the new major version differs from the current major version.
- **Minor not selected**: Skip any package where the new minor version differs (but major is the same).
- **Patch not selected**: Skip any package where only the patch version differs.
- **Skip .0 patches**: If the latest version ends in `.0` (e.g. `2.1.0`), skip it and keep the current version.
- **Security fixes only**: Cross-reference outdated packages with `$PM audit` output. Only update packages that appear in the audit report.
- **Dry run**: Run the full discovery and version-check steps, display a summary table of what would change, then stop without modifying any files or creating a branch.
