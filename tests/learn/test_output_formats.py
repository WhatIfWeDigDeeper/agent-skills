"""Tests for output format validation in learn skill."""

import json
import re
from pathlib import Path


def validate_markdown(file_path: Path) -> tuple[bool, str]:
    """Validate markdown has expected structure."""
    if not file_path.exists():
        return False, "file missing"

    content = file_path.read_text()
    if not content.strip():
        return False, "empty file"

    if re.search(r"^#", content, re.MULTILINE):
        return True, "valid"

    return False, "no heading found"


def validate_mdc(file_path: Path) -> tuple[bool, str]:
    """Validate MDC frontmatter format."""
    if not file_path.exists():
        return False, "file missing"

    content = file_path.read_text()
    lines = content.split("\n")

    if not lines or lines[0] != "---":
        return False, "no frontmatter"

    # Find closing delimiter
    closing_idx = None
    for i, line in enumerate(lines[1:], start=1):
        if line == "---":
            closing_idx = i
            break

    if closing_idx is None:
        return False, "unclosed frontmatter"

    # Check for description field
    frontmatter = "\n".join(lines[1:closing_idx])
    if "description:" in frontmatter:
        return True, "valid"

    return False, "missing description"


def validate_json(file_path: Path) -> tuple[bool, str]:
    """Validate JSON syntax."""
    if not file_path.exists():
        return False, "file missing"

    try:
        content = file_path.read_text()
        json.loads(content)
        return True, "valid"
    except json.JSONDecodeError as e:
        return False, f"invalid json: {e}"


def validate_skill(file_path: Path) -> tuple[bool, str]:
    """Validate SKILL.md format."""
    if not file_path.exists():
        return False, "file missing"

    content = file_path.read_text()
    lines = content.split("\n")

    if not lines or lines[0] != "---":
        return False, "no frontmatter"

    if re.search(r"^name:", content, re.MULTILINE):
        return True, "valid"

    return False, "missing name field"


class TestMarkdownFormat:
    """Test markdown config format validation."""

    def test_valid_markdown_has_heading(self, use_fixture):
        """Valid markdown should have a heading."""
        project = use_fixture("single-configs/claude")
        valid, reason = validate_markdown(project / "CLAUDE.md")
        assert valid, f"Expected valid markdown: {reason}"

    def test_empty_markdown_detected(self, use_fixture):
        """Empty markdown file should be detected."""
        project = use_fixture("malformed/empty-file")
        valid, reason = validate_markdown(project / "CLAUDE.md")
        assert not valid
        assert reason == "empty file"


class TestMDCFormat:
    """Test MDC (Cursor) format validation."""

    def test_valid_mdc_has_frontmatter(self, use_fixture):
        """Valid MDC should have frontmatter with description."""
        project = use_fixture("single-configs/cursor-mdc")
        mdc_files = list((project / ".cursor" / "rules").glob("*.mdc"))
        assert len(mdc_files) == 1

        valid, reason = validate_mdc(mdc_files[0])
        assert valid, f"Expected valid MDC: {reason}"

    def test_mdc_without_frontmatter_detected(self, use_fixture):
        """MDC without frontmatter should be detected."""
        project = use_fixture("malformed/missing-frontmatter")
        mdc_files = list((project / ".cursor" / "rules").glob("*.mdc"))
        assert len(mdc_files) == 1

        valid, reason = validate_mdc(mdc_files[0])
        assert not valid
        assert reason == "no frontmatter"


class TestJSONFormat:
    """Test JSON config format validation."""

    def test_valid_json_config(self, use_fixture):
        """Valid JSON should parse correctly."""
        project = use_fixture("single-configs/continue")
        valid, reason = validate_json(project / ".continuerc.json")
        assert valid, f"Expected valid JSON: {reason}"

    def test_invalid_json_detected(self, use_fixture):
        """Invalid JSON should be detected."""
        project = use_fixture("malformed/invalid-json")
        valid, reason = validate_json(project / ".continuerc.json")
        assert not valid
        assert "invalid json" in reason

    def test_continue_config_has_custom_instructions(self, use_fixture):
        """Continue config should have customInstructions field."""
        project = use_fixture("single-configs/continue")
        content = json.loads((project / ".continuerc.json").read_text())
        assert "customInstructions" in content


class TestSKILLFormat:
    """Test SKILL.md format validation."""

    def test_valid_skill_has_name_field(self, use_fixture):
        """Valid SKILL.md should have name field."""
        project = use_fixture("with-skills/single-skill")
        skill_files = list(project.rglob("SKILL.md"))
        assert len(skill_files) == 1

        valid, reason = validate_skill(skill_files[0])
        assert valid, f"Expected valid SKILL.md: {reason}"

    def test_skill_without_name_detected(self, use_fixture):
        """SKILL.md without name field should be detected."""
        project = use_fixture("with-skills/malformed-skill")
        skill_files = list(project.rglob("SKILL.md"))
        assert len(skill_files) == 1

        valid, reason = validate_skill(skill_files[0])
        assert not valid
        assert reason == "missing name field"
