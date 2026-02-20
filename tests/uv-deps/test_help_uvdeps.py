"""Tests for help trigger detection and interactive-help.md structure in uv-deps skill."""

import re
from pathlib import Path

import pytest

from conftest import is_help_request, parse_arguments

SKILL_DIR = Path(__file__).parent.parent.parent / "skills" / "uv-deps"

SAMPLE_DEPS = {
    "fastapi": ">=0.100",
    "pydantic": ">=2.0",
    "pytest": ">=7.0",
    "help": ">=1.0.0",  # edge case: package literally named "help"
}


class TestHelpTriggers:
    """Test that help arguments are correctly identified."""

    @pytest.mark.parametrize("args", ["help", "--help", "-h", "?"])
    def test_recognized_help_triggers(self, args):
        """All documented help triggers should be detected."""
        assert is_help_request(args) is True

    @pytest.mark.parametrize("args", ["Help", "HELP", "--HELP", "-H"])
    def test_case_insensitive(self, args):
        """Help triggers should be case-insensitive."""
        assert is_help_request(args) is True

    @pytest.mark.parametrize("args", [" help ", " --help\t", "\t-h "])
    def test_whitespace_trimmed(self, args):
        """Leading/trailing whitespace should be trimmed."""
        assert is_help_request(args) is True


class TestNonHelpArguments:
    """Test that normal arguments are not mistaken for help."""

    @pytest.mark.parametrize("args", [
        "fastapi",
        "fastapi pydantic",
        "django-*",
        ".",
        "help me",
        "typescript --help-me",
        "-help",
        "??",
        "help fastapi",
    ])
    def test_normal_args_not_help(self, args):
        """Normal package arguments should not trigger help."""
        assert is_help_request(args) is False

    def test_empty_string(self):
        """Empty string is not a help request."""
        assert is_help_request("") is False

    def test_whitespace_only(self):
        """Whitespace-only is not a help request."""
        assert is_help_request("   ") is False


class TestHelpVsPackageParsing:
    """Ensure help triggers are checked before argument parsing."""

    @pytest.mark.parametrize("args", ["help", "--help", "-h", "?"])
    def test_help_should_short_circuit_before_parsing(self, args):
        """Help args should be detected before being passed to parse_arguments."""
        assert is_help_request(args) is True

    def test_help_named_package_still_parseable(self):
        """If a package is literally named 'help', parse_arguments handles it.

        The skill checks is_help_request first; only if false does it parse.
        """
        result = parse_arguments("help", SAMPLE_DEPS)
        assert result == ["help"]


class TestInteractiveHelpStructure:
    """Validate interactive-help.md has correct structure for AskUserQuestion."""

    @pytest.fixture(scope="class")
    def help_content(self):
        return (SKILL_DIR / "references" / "interactive-help.md").read_text()

    def test_file_exists(self):
        assert (SKILL_DIR / "references" / "interactive-help.md").exists()

    def test_has_question_1(self, help_content):
        assert "## Question 1" in help_content

    def test_has_conditional_questions(self, help_content):
        """uv-deps has conditional Q2a (update filters) and Q2b (severity filter)."""
        assert "## Question 2a" in help_content
        assert "## Question 2b" in help_content

    @pytest.mark.parametrize("question_header,max_options", [
        ("## Question 1", 4),
        ("## Question 2a", 4),
        ("## Question 2b", 4),
    ])
    def test_option_count_within_limit(self, help_content, question_header, max_options):
        """Each question must have at most 4 options (AskUserQuestion limit)."""
        pattern = re.escape(question_header) + r".*?\n(.*?)(?=\n## |\Z)"
        match = re.search(pattern, help_content, re.DOTALL)
        assert match, f"Could not find section {question_header}"
        section = match.group(1)
        table_rows = [
            line for line in section.split("\n")
            if line.startswith("|") and not line.startswith("|--") and not line.startswith("| Option")
        ]
        assert len(table_rows) <= max_options, (
            f"{question_header} has {len(table_rows)} options, max is {max_options}"
        )
        assert len(table_rows) >= 2, (
            f"{question_header} has {len(table_rows)} options, need at least 2"
        )

    def test_q1_is_single_select(self, help_content):
        """Question 1 (workflow type) should use multiSelect: false."""
        q1_section = help_content.split("## Question 2")[0]
        assert "multiSelect: false" in q1_section

    def test_q2a_is_multi_select(self, help_content):
        """Question 2a (update filters) should use multiSelect: true."""
        q2a_start = help_content.index("## Question 2a")
        q2b_start = help_content.index("## Question 2b")
        q2a_section = help_content[q2a_start:q2b_start]
        assert "multiSelect: true" in q2a_section

    def test_q2b_is_multi_select(self, help_content):
        """Question 2b (severity filter) should use multiSelect: true."""
        q2b_start = help_content.index("## Question 2b")
        q2b_section = help_content[q2b_start:]
        assert "multiSelect: true" in q2b_section
