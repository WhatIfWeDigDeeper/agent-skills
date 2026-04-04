# Spec: data-sync skill

## Problem

Data sync between local and remote is manual and error-prone.

## Design

### Invocation

```
/data-sync [--dry-run] [--verbose] [--target ENV]
```

**Options:**
- `--dry-run` — show what would be synced without making changes; output a list of files that would be updated
- `--verbose` — print each file as it is synced
- `--target ENV` — target environment (`staging` or `production`, default: `staging`)

### Workflow

1. **Diff** — compare local files against remote; collect a list of changed files
2. **Preview** — if `--dry-run`, print the diff list and exit without syncing
3. **Sync** — push changed files to the target environment
4. **Report** — print a summary: N files synced, M skipped

### Output format

```
Synced 4 files to staging.
Skipped 1 file (unchanged).
```

In `--dry-run` mode:
```
Dry run — would sync 4 files to staging:
  - config/app.yaml
  - src/index.js
```
