# Tasks: Validation Script Discovery

## Task 1: Update SKILL.md Step 7

**File:** `skills/js-deps/SKILL.md` (lines 80-89)

- Replace "run available commands using `$PM run <script>` in order: build, lint, test. Skip any that don't exist." with the discovery table (exact + prefix matches per category)
- Add instruction to present discovered scripts to user and confirm before running
- Add trust boundary note about worktree isolation
- Keep existing failure semantics and revert logic unchanged

## Task 2: Update error categorization in update-workflow.md

**File:** `skills/js-deps/references/update-workflow.md` (line 117-129)

- Change "Build" / "Lint" / "Test" labels to "Build scripts" / "Lint scripts" / "Test scripts" to reflect that discovered names may differ

## Task 3: Expand `detect_validation_scripts` in conftest.py

**File:** `tests/js-deps/conftest.py` (lines 147-169)

- Add `typecheck` to build candidates, `format` to lint candidates, `tests` to test candidates
- Add prefix matching: after checking exact names, scan for `build:*`, `lint:*`, `test:*`, `test.*` prefixed scripts
- Return all matches per category (list) rather than just the first, so the user can choose — update return type from `dict[str, str | None]` to `dict[str, list[str]]`

## Task 4: Add test fixtures and cases

**Files:**
- `tests/js-deps/conftest.py` — add `validation/prefix-names` fixture with scripts: `test:unit`, `test:integration`, `lint:fix`, `build:prod`
- `tests/js-deps/conftest.py` — add `validation/lifecycle` fixture with scripts: `preinstall`, `postinstall`, `prepare`, `build`
- `tests/js-deps/test_pm_edge_cases.py` — add to `TestValidationScripts`:
  - `test_detects_prefix_scripts`: verifies `test:unit` → test category, `lint:fix` → lint, `build:prod` → build
  - `test_ignores_lifecycle_scripts`: verifies `preinstall`/`postinstall`/`prepare` not matched, but `build` still is
  - Update existing tests if return type changes from `str | None` to `list[str]`

## Task 5: Verify

- Run `uv run --with pytest pytest tests/js-deps/` — all tests pass
- `grep -r "in order: build, lint, test" skills/js-deps/` returns no results
- Read updated Step 7 to confirm discovery, confirmation, and trust boundary are all present
