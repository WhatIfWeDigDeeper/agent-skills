"""Pytest fixtures for js-deps skill tests."""

import fnmatch
import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Generator

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def generate_package_json(
    name: str = "test-project",
    dependencies: dict | None = None,
    dev_dependencies: dict | None = None,
    scripts: dict | None = None,
    package_manager: str | None = None,
) -> str:
    """Generate a package.json file."""
    pkg = {"name": name, "version": "1.0.0"}
    if dependencies:
        pkg["dependencies"] = dependencies
    if dev_dependencies:
        pkg["devDependencies"] = dev_dependencies
    if scripts:
        pkg["scripts"] = scripts
    if package_manager:
        pkg["packageManager"] = package_manager
    return json.dumps(pkg, indent=2)


# --- Bash script helpers (matching SKILL.md) ---


def run_pm_detection_script(directory: Path) -> str:
    """Run the lock file detection script from SKILL.md step 2."""
    # Exact script from SKILL.md step 2
    script = """
    if [ -f "bun.lockb" ]; then PM="bun"
    elif [ -f "pnpm-lock.yaml" ]; then PM="pnpm"
    elif [ -f "yarn.lock" ]; then PM="yarn"
    else PM="npm"
    fi
    echo "$PM"
    """
    result = subprocess.run(
        ["bash", "-c", script],
        cwd=directory,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def run_package_discovery_script(directory: Path) -> list[str]:
    """Run the package discovery script from SKILL.md step 4."""
    # Exact script from SKILL.md step 4
    script = """
    find . -name "package.json" -not -path "*/node_modules/*" -type f
    """
    result = subprocess.run(
        ["bash", "-c", script],
        cwd=directory,
        capture_output=True,
        text=True,
    )
    return sorted(line for line in result.stdout.strip().split("\n") if line)


# --- Python helpers ---


def detect_package_manager_field(directory: Path) -> str | None:
    """Read packageManager field from package.json (takes precedence over lock files)."""
    pkg_json = directory / "package.json"
    if not pkg_json.exists():
        return None
    try:
        data = json.loads(pkg_json.read_text())
        pm_field = data.get("packageManager", "")
        if pm_field:
            return pm_field.split("@")[0]
    except (json.JSONDecodeError, KeyError):
        pass
    return None


def detect_package_manager(directory: Path) -> str:
    """Full package manager detection: packageManager field first, then lock files."""
    field = detect_package_manager_field(directory)
    if field:
        return field
    return run_pm_detection_script(directory)


HELP_TRIGGERS = {"help", "--help", "-h", "?"}


def is_help_request(args: str) -> bool:
    """Check if arguments are a help request per SKILL.md."""
    return args.strip().lower() in HELP_TRIGGERS if args and args.strip() else False


def classify_workflow(request_text: str) -> str:
    """Classify user request as 'audit' or 'update' per SKILL.md workflow selection."""
    audit_keywords = {"audit", "cve", "vulnerabilities", "vulnerability", "security"}
    update_keywords = {"update", "upgrade", "latest", "modernize"}
    lower = request_text.lower()
    words = set(lower.split())
    if words & audit_keywords:
        return "audit"
    if words & update_keywords:
        return "update"
    return "unknown"


def parse_arguments(args: str, dependencies: dict) -> list[str]:
    """Parse package arguments per SKILL.md step 6.

    - Specific packages: "jest @types/jest" → ["jest", "@types/jest"]
    - All packages: "." → all dependency names
    - Glob patterns: "@testing-library/* jest*" → matching dependency names
    """
    if not args or not args.strip():
        return []

    args = args.strip()
    if args == ".":
        return sorted(dependencies.keys())

    tokens = args.split()
    result = []
    for token in tokens:
        if any(c in token for c in "*?["):
            # Glob pattern: expand against dependency names
            matches = [dep for dep in dependencies if fnmatch.fnmatch(dep, token)]
            result.extend(sorted(matches))
        else:
            result.append(token)
    return result


def detect_validation_scripts(package_json_path: Path) -> dict[str, str | None]:
    """Detect available validation scripts per SKILL.md step 7."""
    build_names = {"build", "compile", "tsc"}
    lint_names = {"lint", "check", "eslint"}
    test_names = {"test", "jest", "vitest"}

    try:
        data = json.loads(package_json_path.read_text())
        scripts = data.get("scripts", {})
    except (json.JSONDecodeError, FileNotFoundError):
        return {"build": None, "lint": None, "test": None}

    def find_script(candidates: set) -> str | None:
        for name in candidates:
            if name in scripts:
                return name
        return None

    return {
        "build": find_script(build_names),
        "lint": find_script(lint_names),
        "test": find_script(test_names),
    }


# --- Fixtures ---


@pytest.fixture(scope="session", autouse=True)
def setup_fixtures() -> Generator[Path, None, None]:
    """Create all test fixtures once per session."""
    if FIXTURES_DIR.exists():
        shutil.rmtree(FIXTURES_DIR)
    FIXTURES_DIR.mkdir(parents=True)

    deps = {
        "react": "^18.2.0",
        "express": "^4.18.2",
        "@testing-library/react": "^14.0.0",
        "@testing-library/jest-dom": "^6.0.0",
        "jest": "^29.7.0",
        "jest-environment-jsdom": "^29.7.0",
        "lodash": "^4.17.21",
    }
    dev_deps = {
        "@types/jest": "^29.5.0",
        "@types/react": "^18.2.0",
        "typescript": "^5.3.0",
    }
    all_scripts = {
        "build": "tsc",
        "lint": "eslint .",
        "test": "jest",
    }

    # 1. Package manager detection fixtures
    pm = FIXTURES_DIR / "pm-detection"

    # bun
    (pm / "bun").mkdir(parents=True)
    (pm / "bun" / "package.json").write_text(generate_package_json("bun-project", deps))
    (pm / "bun" / "bun.lockb").write_bytes(b"\x00")  # binary file

    # pnpm
    (pm / "pnpm").mkdir(parents=True)
    (pm / "pnpm" / "package.json").write_text(generate_package_json("pnpm-project", deps))
    (pm / "pnpm" / "pnpm-lock.yaml").write_text("lockfileVersion: '6.0'\n")

    # yarn
    (pm / "yarn").mkdir(parents=True)
    (pm / "yarn" / "package.json").write_text(generate_package_json("yarn-project", deps))
    (pm / "yarn" / "yarn.lock").write_text("# yarn lockfile v1\n")

    # npm
    (pm / "npm").mkdir(parents=True)
    (pm / "npm" / "package.json").write_text(generate_package_json("npm-project", deps))
    (pm / "npm" / "package-lock.json").write_text('{"lockfileVersion": 3}\n')

    # No lock file (defaults to npm)
    (pm / "no-lockfile").mkdir(parents=True)
    (pm / "no-lockfile" / "package.json").write_text(generate_package_json("no-lock", deps))

    # packageManager field (should take precedence)
    (pm / "field-pnpm").mkdir(parents=True)
    (pm / "field-pnpm" / "package.json").write_text(
        generate_package_json("field-project", deps, package_manager="pnpm@8.6.0")
    )

    # packageManager field overrides conflicting lock file
    (pm / "field-overrides-lockfile").mkdir(parents=True)
    (pm / "field-overrides-lockfile" / "package.json").write_text(
        generate_package_json("override-project", deps, package_manager="pnpm@8.6.0")
    )
    (pm / "field-overrides-lockfile" / "yarn.lock").write_text("# yarn lockfile v1\n")

    # Multiple lock files (bun wins by precedence)
    (pm / "multiple-lockfiles").mkdir(parents=True)
    (pm / "multiple-lockfiles" / "package.json").write_text(
        generate_package_json("multi-lock", deps)
    )
    (pm / "multiple-lockfiles" / "bun.lockb").write_bytes(b"\x00")
    (pm / "multiple-lockfiles" / "yarn.lock").write_text("# yarn lockfile v1\n")

    # 2. Package discovery fixtures
    disco = FIXTURES_DIR / "package-discovery"

    # Single root package.json
    (disco / "single").mkdir(parents=True)
    (disco / "single" / "package.json").write_text(generate_package_json("single"))

    # Monorepo with multiple packages
    mono = disco / "monorepo"
    (mono).mkdir(parents=True)
    (mono / "package.json").write_text(generate_package_json("monorepo-root"))
    (mono / "packages" / "frontend").mkdir(parents=True)
    (mono / "packages" / "frontend" / "package.json").write_text(
        generate_package_json("frontend", {"react": "^18.2.0"})
    )
    (mono / "packages" / "backend").mkdir(parents=True)
    (mono / "packages" / "backend" / "package.json").write_text(
        generate_package_json("backend", {"express": "^4.18.2"})
    )

    # With node_modules (should be excluded)
    nm = disco / "with-node-modules"
    (nm).mkdir(parents=True)
    (nm / "package.json").write_text(generate_package_json("with-nm"))
    (nm / "node_modules" / "some-pkg").mkdir(parents=True)
    (nm / "node_modules" / "some-pkg" / "package.json").write_text(
        generate_package_json("some-pkg")
    )

    # Deeply nested
    deep = disco / "deep-nesting"
    (deep / "libs" / "core" / "sub").mkdir(parents=True)
    (deep / "package.json").write_text(generate_package_json("deep-root"))
    (deep / "libs" / "core" / "package.json").write_text(
        generate_package_json("core")
    )
    (deep / "libs" / "core" / "sub" / "package.json").write_text(
        generate_package_json("sub")
    )

    # No package.json
    (disco / "empty").mkdir(parents=True)
    (disco / "empty" / ".gitkeep").touch()

    # 3. Argument parsing fixtures
    args_dir = FIXTURES_DIR / "arguments"
    (args_dir).mkdir(parents=True)
    (args_dir / "package.json").write_text(
        generate_package_json("args-project", deps, dev_deps)
    )

    # 4. Validation script fixtures
    val = FIXTURES_DIR / "validation"

    # All scripts
    (val / "all-scripts").mkdir(parents=True)
    (val / "all-scripts" / "package.json").write_text(
        generate_package_json("all-scripts", scripts=all_scripts)
    )

    # Partial scripts (build + test only)
    (val / "partial-scripts").mkdir(parents=True)
    (val / "partial-scripts" / "package.json").write_text(
        generate_package_json("partial", scripts={"build": "tsc", "test": "jest"})
    )

    # No scripts
    (val / "no-scripts").mkdir(parents=True)
    (val / "no-scripts" / "package.json").write_text(
        generate_package_json("no-scripts")
    )

    # Alternative script names (compile, check, vitest)
    (val / "alt-names").mkdir(parents=True)
    (val / "alt-names" / "package.json").write_text(
        generate_package_json(
            "alt-names",
            scripts={"compile": "tsc -b", "check": "biome check .", "vitest": "vitest run"},
        )
    )

    # Only dev scripts (start, dev - no validation)
    (val / "dev-only").mkdir(parents=True)
    (val / "dev-only" / "package.json").write_text(
        generate_package_json("dev-only", scripts={"start": "node .", "dev": "nodemon ."})
    )

    # 5. Edge case fixtures
    edge = FIXTURES_DIR / "edge-cases"

    # Empty package.json
    (edge / "empty-package-json").mkdir(parents=True)
    (edge / "empty-package-json" / "package.json").write_text("{}")

    # Malformed JSON
    (edge / "malformed-json").mkdir(parents=True)
    (edge / "malformed-json" / "package.json").write_text('{ "name": "broken"')

    # package.json with no dependencies
    (edge / "no-deps").mkdir(parents=True)
    (edge / "no-deps" / "package.json").write_text(
        generate_package_json("no-deps", scripts={"build": "echo ok"})
    )

    # packageManager field with no version
    (edge / "pm-no-version").mkdir(parents=True)
    (edge / "pm-no-version" / "package.json").write_text(
        generate_package_json("pm-no-ver", package_manager="yarn")
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
    """Factory fixture to copy a fixture to temp dir."""

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
