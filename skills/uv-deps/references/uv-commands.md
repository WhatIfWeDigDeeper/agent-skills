# uv Command Reference

## Verify CLI and Connectivity

| Command | Verifies |
|---------|----------|
| `uv --version` | CLI availability |
| `uvx --version` | uvx tool runner availability |
| `uv pip index versions pip` | PyPI connectivity |

## Environment Management

| Command | Purpose |
|---------|---------|
| `uv sync --extra dev` | Install all deps including dev extras (`[project.optional-dependencies]`) |
| `uv sync --group dev` | Install all deps including dev group (`[dependency-groups]`, PEP 735) |
| `uv lock` | Regenerate lockfile from pyproject.toml |
| `uv lock --upgrade-package <pkg>` | Upgrade specific package in lockfile |

## Package Operations

| Command | Purpose |
|---------|---------|
| `uv add <pkg>==<version>` | Add or update a production dependency with exact pin |
| `uv add --optional dev <pkg>==<version>` | Add or update a dev dependency (in `[project.optional-dependencies] dev`) |
| `uv add --group dev <pkg>==<version>` | Add or update a dev dependency (in `[dependency-groups] dev`, PEP 735) |
| `uv remove <pkg>` | Remove a package |
| `uv pip list --outdated` | Show outdated packages in current environment |
| `uv pip show <pkg>` | Show installed package info (version, location, deps) |
| `uv pip index versions <pkg>` | Show all available versions on PyPI |

## Security Audit (via pip-audit)

pip-audit is run via `uvx` to avoid installing it as a project dependency. Because Python 3.14's `ensurepip` is incompatible with pip-audit's internal venv creation, always use the `uv export` pipeline pattern:

> **Version pinning:** `uvx pip-audit` runs the latest release unpinned. If your security policy requires pinning, use `uvx 'pip-audit>=2,<3'` and update the bound on major releases.

```bash
uv export --frozen | uvx pip-audit --strict --format json --desc -r /dev/stdin --disable-pip --no-deps
```

The `--disable-pip` flag skips pip-audit's internal venv creation (requires hashed requirements, which `uv export` provides by default). The `--no-deps` flag skips dependency resolution since the lockfile already contains the full dependency tree. Use `--format json --desc` for machine-parseable output with vulnerability descriptions.

### pip-audit Flags

| Flag | Purpose |
|------|---------|
| `--strict` | Treat warnings as errors (non-zero exit on vulnerabilities) |
| `--format json` | JSON output for parsing |
| `--desc` | Include vulnerability descriptions |
| `--disable-pip` | Skip internal pip/venv usage (requires hashed `-r` input) |
| `--no-deps` | Skip dependency resolution (use with full lockfile export) |
| `--ignore-vuln <ID>` | Ignore a specific vulnerability by ID |

Multiple `--ignore-vuln` flags can be combined:
```bash
uv export --frozen | uvx pip-audit --strict -r /dev/stdin --disable-pip --no-deps --ignore-vuln PYSEC-2024-001 --ignore-vuln GHSA-xxxx-xxxx-xxxx
```

## Validation

Detect available tools from `pyproject.toml` dependencies and run via `uv run`:

| Command | Tool | Purpose |
|---------|------|---------|
| `uv run mypy <paths>` | mypy | Type checking |
| `uv run ruff check <paths>` | ruff | Linting and formatting checks |
| `uv run pytest` | pytest | Unit and integration tests |

Determine `<paths>` by checking `pyproject.toml` tool config sections (e.g., `[tool.mypy]`, `[tool.ruff]`) for configured paths, then fall back to the project directory structure.

If the project uses a task runner (e.g., `Makefile`, `tox.ini`, `noxfile.py`, or `[project.scripts]` in pyproject.toml), prefer those instead.
