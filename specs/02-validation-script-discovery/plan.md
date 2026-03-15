# Plan: Improve js-deps Step 7 Script Discovery

## Problem

Security audit (skills.sh Agent Trust Hub, 2026-03-15) flagged that js-deps executes arbitrary project-defined scripts during validation without documenting the trust decision or confirming with the user. The current Step 7 says "run build, lint, test — skip any that don't exist" which:

1. Misses common script name variants (`compile`, `typecheck`, `test:unit`, `test:integration`, `lint:fix`, `format:check`)
2. Runs scripts without confirming with the user first
3. Doesn't document the trust boundary around executing project-defined code

Note: 6 of 7 total audit findings across js-deps and pr-comments were already fixed (dangerouslyDisableSandbox removed in 8853f50, prompt injection defenses added in 3a58353) or are inherent to the workflow (registry downloads). This is the only actionable finding.

## Design

### Script Discovery

Read the `scripts` object from each `package.json` and classify into three categories using exact matches and prefix matches:

| Category | Exact matches | Prefix matches |
|----------|--------------|----------------|
| Build | `build`, `compile`, `tsc`, `typecheck` | `build:*` |
| Lint | `lint`, `check`, `format`, `format:check` | `lint:*` |
| Test | `test`, `tests` | `test:*`, `test.*` |

Explicitly ignore: lifecycle scripts (`preinstall`, `postinstall`, `prepare`), dev server scripts (`dev`, `start`, `serve`, `watch`).

### User Confirmation

Before executing, present discovered scripts in a table grouped by category and ask the user to confirm which to run. If no scripts match, note that validation is skipped for that directory.

### Trust Boundary

Add a note: validation scripts are project-defined code executing in a disposable worktree. The worktree branch is never merged automatically — changes require PR review.

### Failure Semantics (unchanged)

- Build script failure → hard failure, revert the package
- Lint/test script failure → soft failure, report and continue

## Files to Modify

1. `skills/js-deps/SKILL.md` — Step 7 (lines 80-89): replace hardcoded script names with discovery + confirmation flow
2. `skills/js-deps/references/update-workflow.md` — line 117: update error categorization table
3. `tests/js-deps/conftest.py` — `detect_validation_scripts` (lines 147-169): expand matching, add prefix support
4. `tests/js-deps/conftest.py` — fixtures (line 301+): add `validation/prefix-names` fixture
5. `tests/js-deps/test_pm_edge_cases.py` — `TestValidationScripts`: add prefix and lifecycle test cases
