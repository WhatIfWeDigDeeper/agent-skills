# Security scanning

This file provides guidance when working in `evals/security/`. It auto-loads in Claude Code when you read or edit files in this directory.

## Purpose

`evals/security/` pins the current per-skill output of `snyk-agent-scan` so CI catches *regressions* (new findings, severity escalations) without forcing every existing finding to be fixed first. Many findings are scanner heuristics that fire on patterns the skill genuinely needs (`gh pr view`, external CLI handoff). The baseline approach lets us ship well-mitigated skills while preventing silent expansion of the finding surface.

## Files

- `scan.sh` — runs `uvx snyk-agent-scan@latest --skills <path>` per flagged skill, parses findings, diffs against the baseline. Exits 1 on regression.
- `<skill>.baseline.json` — one per flagged skill. Schema: `scanner`, `scanner_version`, `skill`, `skill_version`, `findings: [{id, severity}]`, `captured_at`, optional `notes`.

## Rules

- **Refresh the baseline in the same PR as a security-relevant skill change.** If you tighten a skill's validation, boundary markers, or mitigation surface, re-run `bash evals/security/scan.sh --update-baselines --confirm` and commit the updated `<skill>.baseline.json` in the same PR. Drifted baselines silently mask future regressions.
- **Removing a finding from a baseline requires a PR comment explaining why the underlying mitigation actually closed it** — vs. the scanner just moved on between versions. Without that note, a reviewer cannot tell whether the security improvement is real or whether the scanner happened to skip the file.
- **Adding a new skill that ingests untrusted content** — add a baseline file in the same PR. Use the same schema. Even if the scan returns zero findings, write `"findings": []` so the harness knows about the skill.
- **Bumping the scanner version** — pin the new version in `scan.sh` (e.g., `SCANNER_PKG="snyk-agent-scan==0.6.0"`), refresh all baselines, and call out the version change in the PR description. Heuristics may shift between scanner releases; expect baseline churn.
- **Severity escalations are regressions** — if a finding's severity goes up (e.g., `medium` → `high`), `scan.sh` fails CI even when the finding ID is unchanged. Either fix the underlying issue or update the baseline with a justification comment.

## Running locally

```bash
# CI mode — diff scan output against baseline; exit 1 on regression
bash evals/security/scan.sh

# Just print parsed findings, no diff
bash evals/security/scan.sh --scan-only

# Rewrite baselines from current scan output (manual baseline refresh)
bash evals/security/scan.sh --update-baselines --confirm
```

The first run of `uvx snyk-agent-scan` in a fresh environment downloads the package and can take 20–30s. Subsequent runs use the cached version.

## Out of scope

- The harness does not run prompt-injection eval fixtures. Those would live under `evals/<skill>/` if introduced.
- The harness does not gate on findings the scanner emits as `info` or unknown severity. Only `low`/`medium`/`high`/`critical` are tracked.
