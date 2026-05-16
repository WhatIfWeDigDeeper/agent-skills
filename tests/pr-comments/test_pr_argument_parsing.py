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
        assert result == {"auto": True, "max_iterations": 10, "remaining_args": ""}

    def test_auto_flag_with_count(self):
        result = parse_auto_flag("--auto 5")
        assert result == {"auto": True, "max_iterations": 5, "remaining_args": ""}

    def test_auto_flag_count_of_one(self):
        result = parse_auto_flag("--auto 1")
        assert result == {"auto": True, "max_iterations": 1, "remaining_args": ""}

    def test_auto_flag_with_pr_number(self):
        """--auto and a PR number together: PR number is preserved in remaining_args."""
        result = parse_auto_flag("42 --auto")
        assert result == {"auto": True, "max_iterations": 10, "remaining_args": "42"}

    def test_auto_flag_with_hash_prefixed_pr_number_trailing(self):
        """#42 --auto should enable auto mode; #42 preserved in remaining_args."""
        result = parse_auto_flag("#42 --auto")
        assert result == {"auto": True, "max_iterations": 10, "remaining_args": "#42"}

    def test_auto_flag_with_hash_prefixed_pr_number_leading(self):
        """--auto #42 should enable auto mode; #42 preserved in remaining_args."""
        result = parse_auto_flag("--auto #42")
        assert result == {"auto": True, "max_iterations": 10, "remaining_args": "#42"}

    def test_auto_flag_with_count_and_pr_number(self):
        result = parse_auto_flag("--auto 5 42")
        assert result == {"auto": True, "max_iterations": 5, "remaining_args": "42"}

    def test_no_flags_empty_defaults_to_auto(self):
        """Empty args default to auto mode."""
        result = parse_auto_flag("")
        assert result == {"auto": True, "max_iterations": 10, "remaining_args": ""}

    def test_no_flags_pr_number_only_defaults_to_auto(self):
        """Bare PR number with no flags defaults to auto mode."""
        result = parse_auto_flag("42")
        assert result == {"auto": True, "max_iterations": 10, "remaining_args": "42"}

    def test_auto_zero_rejected_in_auto_mode(self):
        """--auto 0 is treated as --max 0; 0 fails ^[1-9][0-9]{0,3}$ → rejected, not silently dropped."""
        with pytest.raises(ValueError, match=r"Invalid --max value: 0\."):
            parse_auto_flag("--auto 0")

    def test_auto_negative_not_treated_as_count(self):
        """Negative numbers are not consumed as count; land in remaining_args."""
        result = parse_auto_flag("--auto -1")
        assert result == {"auto": True, "max_iterations": 10, "remaining_args": "-1"}


class TestManualFlagParsing:
    """Test --manual flag parsing per SKILL.md."""

    def test_manual_flag_alone(self):
        result = parse_auto_flag("--manual")
        assert result == {"auto": False, "max_iterations": 10, "remaining_args": ""}

    def test_manual_flag_with_pr_number_trailing(self):
        result = parse_auto_flag("42 --manual")
        assert result == {"auto": False, "max_iterations": 10, "remaining_args": "42"}

    def test_manual_flag_with_pr_number_leading(self):
        result = parse_auto_flag("--manual 42")
        assert result == {"auto": False, "max_iterations": 10, "remaining_args": "42"}

    def test_manual_flag_with_hash_prefixed_pr(self):
        result = parse_auto_flag("--manual #42")
        assert result == {"auto": False, "max_iterations": 10, "remaining_args": "#42"}

    def test_manual_overrides_auto(self):
        """--manual after --auto sets mode to manual."""
        result = parse_auto_flag("--auto --manual")
        assert result["auto"] is False

    def test_manual_is_sticky_against_later_auto(self):
        """--manual is sticky: a later --auto does NOT re-enable auto mode."""
        result = parse_auto_flag("--manual --auto")
        assert result["auto"] is False

    def test_manual_does_not_consume_following_number(self):
        """--manual does not consume a following PR number as an iteration cap."""
        result = parse_auto_flag("--manual 42")
        assert result["remaining_args"] == "42"
        assert result["max_iterations"] == 10


class TestCombinedAutoAndPRNumberParsing:
    """End-to-end tests: parse --auto tokens then pass remaining_args to parse_pr_argument."""

    def test_auto_with_pr_number_trailing(self):
        """'42 --auto' → remaining_args '42' → PR number 42."""
        remaining = parse_auto_flag("42 --auto")["remaining_args"]
        assert parse_pr_argument(remaining) == {"type": "pr_number", "number": 42}

    def test_auto_with_pr_number_leading_ambiguous(self):
        """'--auto 42' is ambiguous — 42 is consumed as the iteration count, not a PR number.
        Users should write '--auto 5 42' (count then PR) or '42 --auto' to disambiguate."""
        parsed = parse_auto_flag("--auto 42")
        assert parsed["auto"] is True
        assert parsed["max_iterations"] == 42
        assert parsed["remaining_args"] == ""
        assert parse_pr_argument(parsed["remaining_args"]) == {"type": "detect"}

    def test_auto_count_with_pr_number(self):
        """'--auto 5 42' → remaining_args '42' → PR number 42."""
        remaining = parse_auto_flag("--auto 5 42")["remaining_args"]
        assert parse_pr_argument(remaining) == {"type": "pr_number", "number": 42}

    def test_auto_with_hash_prefixed_pr_trailing(self):
        """'#42 --auto' → remaining_args '#42' → PR number 42."""
        remaining = parse_auto_flag("#42 --auto")["remaining_args"]
        assert parse_pr_argument(remaining) == {"type": "pr_number", "number": 42}

    def test_auto_with_hash_prefixed_pr_leading(self):
        """'--auto #42' → remaining_args '#42' → PR number 42."""
        remaining = parse_auto_flag("--auto #42")["remaining_args"]
        assert parse_pr_argument(remaining) == {"type": "pr_number", "number": 42}

    def test_auto_alone_detects_from_branch(self):
        """'--auto' with no PR number → remaining_args '' → detect from branch."""
        remaining = parse_auto_flag("--auto")["remaining_args"]
        assert parse_pr_argument(remaining) == {"type": "detect"}
