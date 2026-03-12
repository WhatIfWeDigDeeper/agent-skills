"""Tests for PR argument parsing in pr-comments skill."""

import pytest

from conftest import is_pr_number, parse_pr_argument


class TestPRNumberDetection:
    """Test that PR numbers are correctly identified."""

    @pytest.mark.parametrize("args", ["42", "1", "123", "9999"])
    def test_numeric_args_are_pr_numbers(self, args):
        assert is_pr_number(args) is True

    @pytest.mark.parametrize("args", ["help", "abc", "42a", "1.5", "-1", ""])
    def test_non_numeric_args_are_not_pr_numbers(self, args):
        assert is_pr_number(args) is False

    def test_whitespace_around_number(self):
        """PR number with whitespace should still be detected."""
        assert is_pr_number(" 42 ") is True


class TestParseArgument:
    """Test full argument parsing per SKILL.md."""

    def test_empty_detects_from_branch(self):
        result = parse_pr_argument("")
        assert result == {"type": "detect"}

    def test_none_detects_from_branch(self):
        result = parse_pr_argument(None)
        assert result == {"type": "detect"}

    def test_whitespace_detects_from_branch(self):
        result = parse_pr_argument("   ")
        assert result == {"type": "detect"}

    def test_pr_number(self):
        result = parse_pr_argument("42")
        assert result == {"type": "pr_number", "number": 42}

    def test_help_trigger(self):
        result = parse_pr_argument("help")
        assert result == {"type": "help"}

    def test_help_takes_precedence_over_detection(self):
        """Help should be checked before treating as branch detection."""
        result = parse_pr_argument("--help")
        assert result["type"] == "help"

    def test_non_numeric_non_help_detects(self):
        """Unknown text should fall back to branch detection."""
        result = parse_pr_argument("some-branch")
        assert result == {"type": "detect"}
