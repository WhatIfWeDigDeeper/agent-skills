"""Tests for help trigger detection in ship-it skill."""

import re
from pathlib import Path

import pytest

from conftest import is_help_request

SKILL_DIR = Path(__file__).parent.parent.parent / "skills" / "ship-it"


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
        "fix login timeout",
        "add user auth",
        "help me ship",
        "-help",
        "??",
        "no co-author",
    ])
    def test_normal_args_not_help(self, args):
        """Normal ship-it arguments should not trigger help."""
        assert is_help_request(args) is False

    def test_empty_string(self):
        assert is_help_request("") is False

    def test_whitespace_only(self):
        assert is_help_request("   ") is False


class TestOptionsFileStructure:
    """Validate the options.md reference file has correct structure."""

    @pytest.fixture(scope="class")
    def options_content(self):
        return (SKILL_DIR / "references" / "options.md").read_text()

    def test_options_file_exists(self):
        assert (SKILL_DIR / "references" / "options.md").exists()

    def test_has_question_1(self, options_content):
        assert "## Question 1" in options_content

    def test_has_question_2(self, options_content):
        assert "## Question 2" in options_content

    def test_has_how_to_apply(self, options_content):
        assert "## How to Apply" in options_content

    @pytest.mark.parametrize("question_header,max_options", [
        ("## Question 1: Workflow scope", 4),
        ("## Question 2: PR options", 4),
    ])
    def test_option_count_within_limit(self, options_content, question_header, max_options):
        """Each question must have at most 4 options (AskUserQuestion limit)."""
        pattern = re.escape(question_header) + r".*?\n(.*?)(?=\n## |\Z)"
        match = re.search(pattern, options_content, re.DOTALL)
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

    def test_q1_is_single_select(self, options_content):
        """Question 1 should use multiSelect: false."""
        q1_section = options_content.split("## Question 2")[0]
        assert "multiSelect: false" in q1_section

    def test_q2_is_multi_select(self, options_content):
        """Question 2 should use multiSelect: true."""
        q2_start = options_content.index("## Question 2")
        q2_section = options_content[q2_start:]
        assert "multiSelect: true" in q2_section
