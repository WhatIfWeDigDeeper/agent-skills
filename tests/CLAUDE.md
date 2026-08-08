# Tests

This file auto-loads when working in `tests/`.

**Keep test file basenames unique across `tests/`**. Prefer skill-prefixed basenames (for example, `test_prhumanreview_argument_parsing.py`) when a generic name like `test_argument_parsing.py` would otherwise collide with another suite, because pytest collects test directories without `__init__.py` and duplicate basenames can cause import collisions at collection time. When there is no collision risk, following an existing suite's established naming pattern is acceptable.

**When adding a new skill with tests**, create a corresponding workflow under `.github/workflows/` that runs only on path changes to `skills/<skill-name>/**` and `tests/<skill-name>/**`. Prefer the existing `test-<skill-name>-skill.yml` pattern for skill workflows (for example, `test-learn-skill.yml`); `test-<skill-name>.yml` also exists in this repo for some cases such as `uv-deps`. Use `test-learn-skill.yml` as the template — it covers `push`, `pull_request`, and `workflow_dispatch` triggers, runs `uv run --with pytest pytest tests/<skill-name>/ -v`, and uploads fixtures on failure.

**A `tests/<skill>/` suite is CI-gated only if a corresponding workflow exists** (`test-<skill>-skill.yml`, or `test-<skill>.yml` as `uv-deps` uses) — local `pytest` passing doesn't mean CI ran it. When changing a skill's tests, confirm a workflow actually runs that suite; add one if missing.

**Tests that run `git` in a temp dir must strip `GIT_*` from the subprocess env** — git exports `GIT_DIR`/`GIT_WORK_TREE` to hook subprocesses, overriding `cwd=`, so it operates on the real repo. Use `env={k: v for k, v in os.environ.items() if not k.startswith("GIT_")}` plus `GIT_CEILING_DIRECTORIES`. Passes under bare `pytest`; only misfires under a hook.
