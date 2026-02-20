"""Pytest fixtures for uv-deps skill tests."""

import fnmatch
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Generator

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"

HELP_TRIGGERS = {"help", "--help", "-h", "?"}


def is_help_request(args: str) -> bool:
    """Check if arguments are a help request per SKILL.md."""
    return args.strip().lower() in HELP_TRIGGERS if args and args.strip() else False


def classify_workflow(request_text: str) -> str:
    """Classify user request as 'audit', 'update', or 'unknown' per SKILL.md workflow selection."""
    audit_keywords = {"audit", "cve", "vulnerabilities", "vulnerability", "security"}
    update_keywords = {"update", "upgrade", "latest", "modernize"}
    lower = request_text.lower()
    words = set(lower.split())
    if words & audit_keywords:
        return "audit"
    if words & update_keywords:
        return "update"
    return "unknown"


def parse_arguments(args: str, deps: dict) -> list[str]:
    """Parse package arguments per SKILL.md step 5.

    - Specific packages: "fastapi asyncpg" → ["fastapi", "asyncpg"]
    - All packages: "." → all dependency names sorted
    - Glob patterns: "django-*" → matching dependency names
    """
    if not args or not args.strip():
        return []

    args = args.strip()
    if args == ".":
        return sorted(deps.keys())

    tokens = args.split()
    result = []
    for token in tokens:
        if any(c in token for c in "*?["):
            matches = [dep for dep in deps if fnmatch.fnmatch(dep, token)]
            result.extend(sorted(matches))
        else:
            result.append(token)
    return result


def detect_sync_flag(pyproject_content: str) -> str:
    """Determine the correct uv sync flag per SKILL.md step 4.

    Returns '--extra dev', '--group dev', or '' (bare uv sync).
    """
    lines = pyproject_content.split("\n")

    # Check for [project.optional-dependencies] with dev key
    in_optional = False
    for line in lines:
        stripped = line.strip()
        if stripped == "[project.optional-dependencies]":
            in_optional = True
        elif in_optional and stripped.startswith("["):
            in_optional = False
        elif in_optional and (stripped.startswith("dev ") or stripped.startswith("dev=")):
            return "--extra dev"

    # Check for [dependency-groups] with dev key
    in_groups = False
    for line in lines:
        stripped = line.strip()
        if stripped == "[dependency-groups]":
            in_groups = True
        elif in_groups and stripped.startswith("["):
            in_groups = False
        elif in_groups and (stripped.startswith("dev ") or stripped.startswith("dev=")):
            return "--group dev"

    return ""


def has_dependency_section(pyproject_content: str) -> bool:
    """Check if pyproject.toml has at least one dependency section per SKILL.md step 3."""
    # Check for optional-dependencies or dependency-groups table headers
    if any(
        m in pyproject_content
        for m in ["[project.optional-dependencies]", "[dependency-groups]"]
    ):
        return True

    # Check for dependencies key under [project]
    lines = pyproject_content.split("\n")
    in_project = False
    for line in lines:
        stripped = line.strip()
        if stripped == "[project]":
            in_project = True
        elif in_project and stripped.startswith("["):
            in_project = False
        elif in_project and stripped.startswith("dependencies"):
            return True

    return False


def run_project_discovery_script(directory: Path) -> list[str]:
    """Run the pyproject.toml discovery bash script from SKILL.md step 3."""
    script = """
    find . -name "pyproject.toml" \\
      -not -path "*/.venv/*" \\
      -not -path "*/.tox/*" \\
      -not -path "*/build/*" \\
      -not -path "*/dist/*" \\
      -type f
    """
    result = subprocess.run(
        ["bash", "-c", script],
        cwd=directory,
        capture_output=True,
        text=True,
    )
    return sorted(line for line in result.stdout.strip().split("\n") if line)


def generate_pyproject_toml(
    name: str = "test-project",
    deps: list[str] | None = None,
    optional_dev: list[str] | None = None,
    group_dev: list[str] | None = None,
) -> str:
    """Generate a pyproject.toml string with specified dependency sections."""
    parts = [f'[project]\nname = "{name}"\nversion = "0.1.0"\nrequires-python = ">=3.12"']

    if deps is not None:
        dep_items = "\n".join(f'  "{d}",' for d in deps)
        parts[-1] += f"\ndependencies = [\n{dep_items}\n]" if dep_items else "\ndependencies = []"

    if optional_dev is not None:
        dev_items = "\n".join(f'  "{d}",' for d in optional_dev)
        parts.append(f"[project.optional-dependencies]\ndev = [\n{dev_items}\n]")

    if group_dev is not None:
        dev_items = "\n".join(f'  "{d}",' for d in group_dev)
        parts.append(f"[dependency-groups]\ndev = [\n{dev_items}\n]")

    return "\n\n".join(parts) + "\n"


# --- Fixtures ---


@pytest.fixture(scope="session", autouse=True)
def setup_fixtures() -> Generator[Path, None, None]:
    """Create all test fixtures once per session."""
    if FIXTURES_DIR.exists():
        shutil.rmtree(FIXTURES_DIR)
    FIXTURES_DIR.mkdir(parents=True)

    # 1. Project discovery fixtures
    disco = FIXTURES_DIR / "project-discovery"

    (disco / "single").mkdir(parents=True)
    (disco / "single" / "pyproject.toml").write_text(
        generate_pyproject_toml("single", deps=["fastapi>=0.100", "pydantic>=2.0"])
    )

    (disco / "optional-deps").mkdir(parents=True)
    (disco / "optional-deps" / "pyproject.toml").write_text(
        generate_pyproject_toml("optional-deps", deps=["fastapi"], optional_dev=["pytest", "ruff"])
    )

    (disco / "dep-groups").mkdir(parents=True)
    (disco / "dep-groups" / "pyproject.toml").write_text(
        generate_pyproject_toml("dep-groups", deps=["fastapi"], group_dev=["pytest", "ruff"])
    )

    mono = disco / "monorepo"
    mono.mkdir(parents=True)
    (mono / "pyproject.toml").write_text(generate_pyproject_toml("root", deps=["fastapi"]))
    (mono / "services" / "api").mkdir(parents=True)
    (mono / "services" / "api" / "pyproject.toml").write_text(
        generate_pyproject_toml("api", deps=["fastapi"])
    )
    (mono / "services" / "worker").mkdir(parents=True)
    (mono / "services" / "worker" / "pyproject.toml").write_text(
        generate_pyproject_toml("worker", deps=["celery"])
    )

    excl = disco / "excluded-dirs"
    excl.mkdir(parents=True)
    (excl / "pyproject.toml").write_text(generate_pyproject_toml("main", deps=["fastapi"]))
    for excluded_dir in [".venv", ".tox", "build", "dist"]:
        (excl / excluded_dir).mkdir(parents=True)
        (excl / excluded_dir / "pyproject.toml").write_text(
            generate_pyproject_toml(f"pkg-{excluded_dir}", deps=["wheel"])
        )

    (disco / "empty").mkdir(parents=True)
    (disco / "empty" / ".gitkeep").touch()

    (disco / "no-deps").mkdir(parents=True)
    (disco / "no-deps" / "pyproject.toml").write_text(
        '[project]\nname = "tool-only"\nversion = "0.1.0"\n\n[tool.ruff]\nline-length = 88\n'
    )

    # 2. Sync flag fixtures
    sync = FIXTURES_DIR / "sync-flags"

    (sync / "bare").mkdir(parents=True)
    (sync / "bare" / "pyproject.toml").write_text(
        generate_pyproject_toml("bare", deps=["fastapi"])
    )

    (sync / "optional-dev").mkdir(parents=True)
    (sync / "optional-dev" / "pyproject.toml").write_text(
        generate_pyproject_toml("opt-dev", deps=["fastapi"], optional_dev=["pytest"])
    )

    (sync / "group-dev").mkdir(parents=True)
    (sync / "group-dev" / "pyproject.toml").write_text(
        generate_pyproject_toml("grp-dev", deps=["fastapi"], group_dev=["pytest"])
    )

    # 3. Argument parsing fixtures
    args_dir = FIXTURES_DIR / "arguments"
    args_dir.mkdir(parents=True)
    (args_dir / "pyproject.toml").write_text(
        generate_pyproject_toml(
            "args-project",
            deps=["fastapi>=0.100", "pydantic>=2.0", "sqlalchemy>=2.0", "django-rest-framework>=3.14"],
            optional_dev=["pytest>=7.0", "ruff>=0.1", "mypy>=1.0"],
        )
    )

    yield FIXTURES_DIR


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for each test."""
    tmp = Path(tempfile.mkdtemp())
    yield tmp
    shutil.rmtree(tmp, ignore_errors=True)


@pytest.fixture
def use_fixture(temp_dir: Path):
    """Factory fixture to copy a fixture directory into temp dir."""

    def _use_fixture(name: str) -> Path:
        src = FIXTURES_DIR / name
        if not src.exists():
            raise ValueError(f"Fixture not found: {src}")
        for item in src.iterdir():
            dest = temp_dir / item.name
            if item.is_dir():
                shutil.copytree(item, dest)
            else:
                shutil.copy2(item, dest)
        return temp_dir

    return _use_fixture
