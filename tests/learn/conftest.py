"""Pytest fixtures for learn skill tests."""

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Generator

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def generate_lines(count: int, prefix: str = "Line") -> str:
    """Generate N lines of content."""
    return "\n".join(f"{prefix} {i}: This is sample content for testing." for i in range(1, count + 1))


def generate_markdown(count: int, title: str = "Test Config") -> str:
    """Generate markdown content with approximately `count` lines."""
    lines = [
        f"# {title}",
        "",
        "## Section 1",
        "",
        generate_lines(count - 10, "Content"),
        "",
        "## Section 2",
        "",
        "Final section content.",
    ]
    return "\n".join(lines)


def generate_mdc(count: int, name: str = "test-rule", description: str = "Test rule description") -> str:
    """Generate MDC (Cursor) content."""
    lines = [
        "---",
        f"description: {description}",
        'globs: "**/*.ts"',
        "---",
        "",
        f"# {name}",
        "",
        generate_lines(count - 10, "Rule content"),
    ]
    return "\n".join(lines)


def generate_json_config(instructions: str = "Test instructions for Continue") -> str:
    """Generate Continue JSON config."""
    config = {
        "models": [],
        "customInstructions": instructions,
        "tabAutocompleteOptions": {"disable": False},
    }
    return json.dumps(config, indent=2)


def generate_skill(name: str, description: str) -> str:
    """Generate a SKILL.md file."""
    return f"""---
name: {name}
description: {description}
---

# {name}

This is the {name} skill.

## Process

### 1. First Step

Do the first thing.
"""


HELP_TRIGGERS = {"help", "--help", "-h", "?"}


def is_help_request(args: str) -> bool:
    """Check if arguments are a help request per SKILL.md."""
    return args.strip().lower() in HELP_TRIGGERS if args and args.strip() else False


@pytest.fixture(scope="session", autouse=True)
def setup_fixtures() -> Generator[Path, None, None]:
    """Create all test fixtures once per session."""
    if FIXTURES_DIR.exists():
        shutil.rmtree(FIXTURES_DIR)
    FIXTURES_DIR.mkdir(parents=True)

    # 1. Empty project
    (FIXTURES_DIR / "empty-project").mkdir()
    (FIXTURES_DIR / "empty-project" / ".gitkeep").touch()

    # 2. Single config fixtures
    single = FIXTURES_DIR / "single-configs"

    # CLAUDE.md
    (single / "claude").mkdir(parents=True)
    (single / "claude" / "CLAUDE.md").write_text(generate_markdown(50, "Claude Config"))

    # GEMINI.md
    (single / "gemini").mkdir(parents=True)
    (single / "gemini" / "GEMINI.md").write_text(generate_markdown(50, "Gemini Config"))

    # AGENTS.md
    (single / "agents").mkdir(parents=True)
    (single / "agents" / "AGENTS.md").write_text(generate_markdown(50, "Agents Config"))

    # .cursorrules
    (single / "cursorrules").mkdir(parents=True)
    (single / "cursorrules" / ".cursorrules").write_text(generate_markdown(50, "Cursor Rules"))

    # .cursor/rules/*.mdc
    (single / "cursor-mdc" / ".cursor" / "rules").mkdir(parents=True)
    (single / "cursor-mdc" / ".cursor" / "rules" / "typescript.mdc").write_text(
        generate_mdc(50, "typescript-rules", "TypeScript coding rules")
    )

    # .github/copilot-instructions.md
    (single / "copilot" / ".github").mkdir(parents=True)
    (single / "copilot" / ".github" / "copilot-instructions.md").write_text(
        generate_markdown(50, "Copilot Instructions")
    )

    # .windsurf/rules/rules.md
    (single / "windsurf" / ".windsurf" / "rules").mkdir(parents=True)
    (single / "windsurf" / ".windsurf" / "rules" / "rules.md").write_text(
        generate_markdown(50, "Windsurf Rules")
    )

    # .continuerc.json
    (single / "continue").mkdir(parents=True)
    (single / "continue" / ".continuerc.json").write_text(
        generate_json_config("Continue configuration instructions")
    )

    # 3. Multi-config fixtures
    multi = FIXTURES_DIR / "multi-configs"

    # Two configs
    (multi / "two-configs").mkdir(parents=True)
    (multi / "two-configs" / "CLAUDE.md").write_text(generate_markdown(50, "Claude Config"))
    (multi / "two-configs" / "GEMINI.md").write_text(generate_markdown(50, "Gemini Config"))

    # Three configs
    (multi / "three-configs" / ".github").mkdir(parents=True)
    (multi / "three-configs" / "CLAUDE.md").write_text(generate_markdown(50, "Claude Config"))
    (multi / "three-configs" / "GEMINI.md").write_text(generate_markdown(50, "Gemini Config"))
    (multi / "three-configs" / ".github" / "copilot-instructions.md").write_text(
        generate_markdown(50, "Copilot Instructions")
    )

    # All configs
    all_configs = multi / "all-configs"
    (all_configs / ".github").mkdir(parents=True)
    (all_configs / ".cursor" / "rules").mkdir(parents=True)
    (all_configs / ".windsurf" / "rules").mkdir(parents=True)
    (all_configs / "CLAUDE.md").write_text(generate_markdown(50, "Claude Config"))
    (all_configs / "GEMINI.md").write_text(generate_markdown(50, "Gemini Config"))
    (all_configs / "AGENTS.md").write_text(generate_markdown(50, "Agents Config"))
    (all_configs / ".cursorrules").write_text(generate_markdown(50, "Cursor Rules"))
    (all_configs / ".cursor" / "rules" / "test.mdc").write_text(generate_mdc(50, "test-rule", "Test rule"))
    (all_configs / ".github" / "copilot-instructions.md").write_text(
        generate_markdown(50, "Copilot Instructions")
    )
    (all_configs / ".windsurf" / "rules" / "rules.md").write_text(generate_markdown(50, "Windsurf Rules"))
    (all_configs / ".continuerc.json").write_text(generate_json_config("All configs test"))

    # 4. Size variations
    sizes = FIXTURES_DIR / "size-variations"

    (sizes / "healthy").mkdir(parents=True)
    (sizes / "healthy" / "CLAUDE.md").write_text(generate_markdown(100, "Healthy Config"))

    (sizes / "warning").mkdir(parents=True)
    (sizes / "warning" / "CLAUDE.md").write_text(generate_markdown(450, "Warning Config"))

    (sizes / "oversized").mkdir(parents=True)
    (sizes / "oversized" / "CLAUDE.md").write_text(generate_markdown(600, "Oversized Config"))

    (sizes / "at-400").mkdir(parents=True)
    (sizes / "at-400" / "CLAUDE.md").write_text(generate_markdown(400, "Threshold 400"))

    (sizes / "at-500").mkdir(parents=True)
    (sizes / "at-500" / "CLAUDE.md").write_text(generate_markdown(500, "Threshold 500"))

    # 5. Malformed fixtures
    malformed = FIXTURES_DIR / "malformed"

    (malformed / "invalid-json").mkdir(parents=True)
    (malformed / "invalid-json" / ".continuerc.json").write_text('{ "customInstructions": "missing closing brace"')

    (malformed / "missing-frontmatter" / ".cursor" / "rules").mkdir(parents=True)
    (malformed / "missing-frontmatter" / ".cursor" / "rules" / "bad.mdc").write_text(
        "# No frontmatter here\nJust content without the required YAML block."
    )

    (malformed / "empty-file").mkdir(parents=True)
    (malformed / "empty-file" / "CLAUDE.md").touch()

    (malformed / "binary-content").mkdir(parents=True)
    (malformed / "binary-content" / "CLAUDE.md").write_bytes(b"\x00\x01\x02\x03Binary content\x00\x00")

    (malformed / "special-chars").mkdir(parents=True)
    (malformed / "special-chars" / "CLAUDE.md").write_text(
        """# Special Characters Test

Content with special chars: $PATH `backticks` "quotes" 'single'
Emoji: 🎉 🚀 ✅
Unicode: café résumé naïve
Escape sequences: \\n \\t \\r
Shell metacharacters: & | ; < > ( ) { } [ ] * ? ~ ! @ # %
"""
    )

    # 6. Cursor variations
    cursor = FIXTURES_DIR / "cursor-variations"

    (cursor / "legacy-only").mkdir(parents=True)
    (cursor / "legacy-only" / ".cursorrules").write_text(generate_markdown(50, "Legacy Cursor Rules"))

    (cursor / "mdc-only" / ".cursor" / "rules").mkdir(parents=True)
    (cursor / "mdc-only" / ".cursor" / "rules" / "one.mdc").write_text(generate_mdc(50, "rule-one", "First rule"))
    (cursor / "mdc-only" / ".cursor" / "rules" / "two.mdc").write_text(generate_mdc(30, "rule-two", "Second rule"))

    (cursor / "both" / ".cursor" / "rules").mkdir(parents=True)
    (cursor / "both" / ".cursorrules").write_text(generate_markdown(50, "Legacy Cursor Rules"))
    (cursor / "both" / ".cursor" / "rules" / "rule.mdc").write_text(generate_mdc(50, "mdc-rule", "MDC format rule"))

    (cursor / "multi-mdc" / ".cursor" / "rules").mkdir(parents=True)
    (cursor / "multi-mdc" / ".cursor" / "rules" / "typescript.mdc").write_text(
        generate_mdc(30, "typescript", "TypeScript rules")
    )
    (cursor / "multi-mdc" / ".cursor" / "rules" / "react.mdc").write_text(generate_mdc(25, "react", "React rules"))
    (cursor / "multi-mdc" / ".cursor" / "rules" / "testing.mdc").write_text(
        generate_mdc(20, "testing", "Testing rules")
    )

    # 7. With skills
    skills = FIXTURES_DIR / "with-skills"

    (skills / "single-skill" / "skills" / "test-skill").mkdir(parents=True)
    (skills / "single-skill" / "CLAUDE.md").write_text(generate_markdown(50, "Project Config"))
    (skills / "single-skill" / "skills" / "test-skill" / "SKILL.md").write_text(
        generate_skill("test-skill", "A test skill for validation")
    )

    (skills / "multi-skill" / "skills" / "build").mkdir(parents=True)
    (skills / "multi-skill" / "skills" / "test-runner").mkdir(parents=True)
    (skills / "multi-skill" / "skills" / "deploy").mkdir(parents=True)
    (skills / "multi-skill" / "CLAUDE.md").write_text(generate_markdown(50, "Project Config"))
    (skills / "multi-skill" / "skills" / "build" / "SKILL.md").write_text(
        generate_skill("build", "Build the project")
    )
    (skills / "multi-skill" / "skills" / "test-runner" / "SKILL.md").write_text(
        generate_skill("test-runner", "Run tests")
    )
    (skills / "multi-skill" / "skills" / "deploy" / "SKILL.md").write_text(
        generate_skill("deploy", "Deploy to production")
    )

    (skills / "nested-skills" / "packages" / "frontend" / "skills" / "component").mkdir(parents=True)
    (skills / "nested-skills" / "packages" / "backend" / "skills" / "api").mkdir(parents=True)
    (skills / "nested-skills" / "CLAUDE.md").write_text(generate_markdown(50, "Project Config"))
    (skills / "nested-skills" / "packages" / "frontend" / "skills" / "component" / "SKILL.md").write_text(
        generate_skill("component", "Create frontend component")
    )
    (skills / "nested-skills" / "packages" / "backend" / "skills" / "api" / "SKILL.md").write_text(
        generate_skill("api", "Create API endpoint")
    )

    (skills / "with-node-modules" / "skills" / "real-skill").mkdir(parents=True)
    (skills / "with-node-modules" / "node_modules" / "some-package" / "skills" / "ignored-skill").mkdir(parents=True)
    (skills / "with-node-modules" / "CLAUDE.md").write_text(generate_markdown(50, "Project Config"))
    (skills / "with-node-modules" / "skills" / "real-skill" / "SKILL.md").write_text(
        generate_skill("real-skill", "Real skill to find")
    )
    (skills / "with-node-modules" / "node_modules" / "some-package" / "skills" / "ignored-skill" / "SKILL.md").write_text(
        generate_skill("ignored-skill", "Should be ignored")
    )

    (skills / "malformed-skill" / "skills" / "bad-skill").mkdir(parents=True)
    (skills / "malformed-skill" / "CLAUDE.md").write_text(generate_markdown(50, "Project Config"))
    (skills / "malformed-skill" / "skills" / "bad-skill" / "SKILL.md").write_text(
        """---
description: A skill missing the name field
---

# Bad Skill

This skill has no name in frontmatter.
"""
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

        # Copy all contents including hidden files
        for item in src.iterdir():
            dest = temp_dir / item.name
            if item.is_dir():
                shutil.copytree(item, dest)
            else:
                shutil.copy2(item, dest)

        return temp_dir

    return _use_fixture


def run_detection_script(directory: Path) -> list[str]:
    """Run the config detection script from SKILL.md and return detected files."""
    # Detection script from SKILL.md lines 42-46
    script = """
    for f in CLAUDE.md GEMINI.md AGENTS.md .cursorrules .github/copilot-instructions.md \
      .windsurf/rules/rules.md .continuerc.json; do
      [ -f "$f" ] && echo "$f"
    done
    find .cursor/rules -name "*.mdc" 2>/dev/null || true
    """
    result = subprocess.run(
        ["bash", "-c", script],
        cwd=directory,
        capture_output=True,
        text=True,
    )
    return [line for line in result.stdout.strip().split("\n") if line]


def run_skill_discovery_script(directory: Path) -> list[str]:
    """Run the skill discovery script from SKILL.md and return skill names."""
    # Skill discovery script from SKILL.md lines 69-73
    script = """
    find . -name "SKILL.md" -type f 2>/dev/null | grep -v node_modules | \
      xargs grep -l "^name:" 2>/dev/null | while read -r f; do
      grep -m1 "^name:" "$f" | sed 's/name: //'
    done
    """
    result = subprocess.run(
        ["bash", "-c", script],
        cwd=directory,
        capture_output=True,
        text=True,
    )
    return [line for line in result.stdout.strip().split("\n") if line]


def classify_size(line_count: int) -> str:
    """Classify file size per SKILL.md thresholds."""
    if line_count < 400:
        return "healthy"
    elif line_count <= 500:
        return "warning"
    else:
        return "oversized"


def get_line_count(file_path: Path) -> int:
    """Get line count of a file."""
    if not file_path.exists():
        return 0
    return len(file_path.read_text().splitlines())
