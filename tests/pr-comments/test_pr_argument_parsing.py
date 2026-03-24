"""Tests for PR argument parsing in pr-comments skill."""

import pytest

from conftest import is_pr_number, parse_auto_flag, parse_pr_argument


class TestPRNumberDetection:
    """Test that PR numbers are correctly identified."""

    @pytest.mark.parametrize("args", ["42", "1", "123", "9999"])
    def test_numeric_args_are_pr_numbers(self, args):
        assert is_pr_number(args) is True

    @pytest.mark.parametrize("args", ["help", "abc", "42a", "1.5", "-1", ""])
    def test_non_numeric_args_are_not_pr_numbers(self, args):
        assert is_pr_number(args) is False

    def test_hash_prefix_is_pr_number(self):
        """#42 should be recognized as a PR number."""
        assert is_pr_number("#42") is True

    def test_hash_only_is_not_pr_number(self):
        """Bare '#' is not a PR number."""
        assert is_pr_number("#") is False

    def test_double_hash_is_not_pr_number(self):
        """##42 should NOT be treated as PR 42 — only a single leading # is stripped."""
        assert is_pr_number("##42") is False

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

    def test_hash_prefix_pr_number(self):
        """#42 should parse as PR number 42."""
        result = parse_pr_argument("#42")
        assert result == {"type": "pr_number", "number": 42}

    def test_hash_only_detects_from_branch(self):
        """Bare '#' is not a PR number — fall back to branch detection."""
        result = parse_pr_argument("#")
        assert result == {"type": "detect"}

    def test_double_hash_detects_from_branch(self):
        """##42 should fall back to branch detection, not parse as PR 42."""
        result = parse_pr_argument("##42")
        assert result == {"type": "detect"}


class TestAutoFlagParsing:
    """Test --auto [N] flag parsing per SKILL.md."""

    def test_auto_flag_alone(self):
        result = parse_auto_flag("--auto")
        assert result == {"auto": True, "max_iterations": 10}

    def test_auto_flag_with_count(self):
        result = parse_auto_flag("--auto 5")
        assert result == {"auto": True, "max_iterations": 5}

    def test_auto_flag_count_of_one(self):
        result = parse_auto_flag("--auto 1")
        assert result == {"auto": True, "max_iterations": 1}

    def test_auto_flag_with_pr_number(self):
        """--auto and a PR number together: auto flag should be detected."""
        result = parse_auto_flag("42 --auto")
        assert result == {"auto": True, "max_iterations": 10}

    def test_auto_flag_with_count_and_pr_number(self):
        result = parse_auto_flag("--auto 5 42")
        assert result == {"auto": True, "max_iterations": 5}

    def test_no_auto_flag_empty(self):
        result = parse_auto_flag("")
        assert result == {"auto": False, "max_iterations": 10}

    def test_no_auto_flag_pr_number_only(self):
        result = parse_auto_flag("42")
        assert result == {"auto": False, "max_iterations": 10}

    def test_auto_zero_not_treated_as_count(self):
        """--auto 0 is not a valid positive count; 0 should not set max_iterations."""
        result = parse_auto_flag("--auto 0")
        assert result == {"auto": True, "max_iterations": 10}

    def test_auto_negative_not_treated_as_count(self):
        """Negative numbers should not be treated as a valid count."""
        result = parse_auto_flag("--auto -1")
        assert result == {"auto": True, "max_iterations": 10}
