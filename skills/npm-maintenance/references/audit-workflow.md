# Security Audit Workflow

This reference extends the shared process in [../SKILL.md](../SKILL.md) with security-specific steps.

## Audit Execution

### Run Security Audit on Each Directory

For each directory containing package.json:
```bash
cd <directory>
npm audit --json > audit-report-<dir-name>.json
```

Collect all audit results into a consolidated report.

### Categorize by Severity

Parse audit results for each directory:

| Severity | Action |
|----------|--------|
| Critical | Immediate action required |
| High | Serious risk, patch ASAP |
| Moderate | Should fix soon |
| Low | Fix when convenient |

### Determine Strategy

Per directory:
- **1-3 packages**: Update sequentially
- **4+ packages**: Use parallel Task subagents (2 packages per agent)

If multiple directories have vulnerabilities, process them in parallel using separate agents.

### Update Packages

For each vulnerable package in each directory:
```bash
cd <directory>
npm install <package>@latest
```

Then validate using the shared validation step.

### Post-Audit Scan

For each directory:
```bash
cd <directory>
npm audit
```

Compare before/after vulnerability counts per directory.

## Parallel Execution

### Per-Directory Parallelization

When multiple directories have vulnerabilities, launch separate Task subagents for each:

```
Task({
  subagent_type: 'general-purpose',
  prompt: 'Audit and fix vulnerabilities in <directory>...',
  run_in_background: true
})
```

### Per-Package Parallelization

Within a directory with >3 vulnerable packages, split into groups:

```
Task({
  subagent_type: 'general-purpose',
  prompt: 'Update packages X, Y in <directory> with full validation...',
  run_in_background: true
})
```

Collect results from all agents before generating final report.

## Report and Prompt

Generate consolidated security report with:
- Vulnerabilities per directory (initial vs remaining)
- Successfully updated packages per directory
- Failed updates with reasons
- Recommendations for remaining issues
- Overall project security status

Prompt user: merge fixes, keep for review, or discard.

## Example Output

```
Security Audit Report
=====================

Scanned Directories: 5
- /api (Express + Prisma)
- /koa-api (Koa + PostgreSQL)
- /hono-api (Hono + Drizzle)
- /parse-server-api (Parse Server)
- /ui (React UI)

Results by Directory:
---------------------

/api: 2 vulnerabilities fixed
  [x] express 4.17.1 -> 4.18.2 (moderate)
  [x] jsonwebtoken 8.5.1 -> 9.0.0 (high)

/ui: No vulnerabilities found

/koa-api: 1 vulnerability (could not fix)
  [ ] koa-router 10.0.0 (no fix available)

Overall: 2/3 vulnerabilities fixed
```
