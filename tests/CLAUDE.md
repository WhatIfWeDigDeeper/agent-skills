## Tests

**Keep test file basenames unique across `tests/`**. Prefer skill-prefixed basenames (for example, `test_prhumanreview_argument_parsing.py`) when a generic name like `test_argument_parsing.py` would otherwise collide with another suite, because pytest collects test directories without `__init__.py` and duplicate basenames can cause import collisions at collection time. When there is no collision risk, following an existing suite's established naming pattern is acceptable.

**When adding a new skill with tests**, create a corresponding `.github/workflows/test-<skill-name>.yml` that runs only on path changes to `skills/<skill-name>/**` and `tests/<skill-name>/**`. Use `test-learn-skill.yml` as the template — it covers `push`, `pull_request`, and `workflow_dispatch` triggers, runs `uv run --with pytest pytest tests/<skill-name>/ -v`, and uploads fixtures on failure.
