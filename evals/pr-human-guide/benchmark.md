# pr-human-guide Benchmark

## Summary

| Configuration | Mean pass rate | Stddev | Min | Max | Mean time (s) | Mean tokens |
|---------------|---------------|--------|-----|-----|---------------|-------------|
| with_skill    | 100%          | ±0%    | 100% | 100% | 42.2s        | 30,038      |
| without_skill | 61%           | ±31%   | 25%  | 100% | 21.3s        | 24,521      |
| **Delta**     | **+39%**      |        |     |     | **+20.9s**   | **+5,517**  |

Skill version: 0.1 | Model: claude-sonnet-4-6 | Evals: 8 | Run date: 2026-04-12

> **Note**: 6 of 8 evals discriminate (1, 2, 3, 4, 5, 6). Evals 7 and 8 are non-discriminating — capable baselines independently produce structured output with correct category names and exact markers for those scenarios. The discriminating evals test format-specific behavior: exact HTML comment markers, SHA-256 diff anchor links, and the exact terminal report format.

> **Performance note**: with_skill runs are slower (+21s) and heavier (+5,517 tokens) than baseline because they read SKILL.md and categories.md before analysis. The quality gain (+39% pass rate) justifies the cost.

> Summary-table Delta values are computed from unrounded means, so they may differ slightly from subtracting the displayed rounded means.

## Eval Results

| # | Name | with_skill | without_skill | Discriminates? |
|---|------|-----------|---------------|----------------|
| 1 | security-changes | 4/4 (100%) | 1/4 (25%) | Yes |
| 2 | config-changes | 4/4 (100%) | 1/4 (25%) | Yes |
| 3 | new-dependency | 4/4 (100%) | 3/4 (75%) | Yes |
| 4 | novel-pattern | 3/3 (100%) | 2/3 (67%) | Yes |
| 5 | no-special-areas | 3/3 (100%) | 1/3 (33%) | Yes |
| 6 | idempotent-rerun | 3/3 (100%) | 2/3 (67%) | Yes |
| 7 | data-model-changes | 4/4 (100%) | 4/4 (100%) | No |
| 8 | concurrency-state | 4/4 (100%) | 4/4 (100%) | No |

Token statistics are computed over all 8 primary (run_number=1) runs per configuration (N=8 each, 16 total).

## Per-Eval Notes

### Eval 1 — `security-changes`

PR adds JWT middleware and role-based access control. with_skill produced a structured Security section with exact `<!-- pr-human-guide -->` markers and SHA-256 diff links. without_skill used a freeform `## Review Notes` heading, no HTML markers, and no diff links — passing only the `updates-pr-description` assertion. **Discriminates on:** marker format, diff link format.

### Eval 2 — `config-changes`

PR modifies a GitHub Actions workflow (staging→production) and widens IAM permissions. with_skill flagged both under Config/Infrastructure and the IAM change under Security. without_skill updated the description with a single prose summary sentence and explicitly noted "No review guide was added to the description." — passing only `updates-pr-description`. **Discriminates on:** structured guide presence, category sections.

### Eval 3 — `new-dependency`

PR adds `node-forge` (crypto) and `aws-sdk` (network) packages plus an encryption module. Both configurations produced correct New Dependencies and Security content. without_skill used ad-hoc markdown headings rather than the required `<!-- pr-human-guide -->` markers, failing the marker assertion. **Discriminates on:** exact HTML comment marker format.

### Eval 4 — `novel-pattern`

PR introduces Result types (ts-results) in a codebase using try/catch + AppError. Both configurations identified the pattern contrast clearly. without_skill additionally found a logic bug in `refundPayment` the skill didn't flag — but used non-standard heading formatting rather than the required markers. **Discriminates on:** exact HTML comment marker format.

### Eval 5 — `no-special-areas`

PR adds bio/role display fields to a React component with a test — no special review areas. with_skill correctly output the "no areas" message with exact markers. without_skill added a "Notes for reviewers" section with suggestions about the User type interface (wrong output format), used no HTML comment markers. **Discriminates on:** exact "no areas" message, marker format.

### Eval 6 — `idempotent-rerun`

PR has an existing `<!-- pr-human-guide -->` block; new commits were pushed. with_skill performed idempotent replace and output the exact "Review guide updated on PR #42: ..." terminal line. without_skill correctly replaced (not appended) the block and reflected the current diff, but omitted the terminal report line entirely. **Discriminates on:** exact terminal report format.

### Eval 7 — `data-model-changes`

PR has a SQL migration with RENAME COLUMN, DROP COLUMN, SET NOT NULL, and a GraphQL schema removing fields. Both configurations independently produced a well-structured Data Model Changes section with correct entries — and notably, the without_skill baseline independently used `<!-- pr-human-guide -->` markers. The data-model scenario is clear enough that a capable baseline handles it without the skill's framework. **Non-discriminating.**

### Eval 8 — `concurrency-state`

PR introduces worker threads with module-level shared mutable state. Both configurations identified the Concurrency/State and Novel Patterns concerns, used `<!-- pr-human-guide -->` markers, and produced the correct terminal format. The without_skill baseline independently produced output indistinguishable from the with_skill run on all tested assertions. **Non-discriminating.**
