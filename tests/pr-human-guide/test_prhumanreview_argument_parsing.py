"""Tests for PR number argument parsing in pr-human-guide skill."""

import pytest

from conftest import parse_pr_argument


class TestPRNumberParsing:
    """Test PR number extraction per SKILL.md Step 1."""

    @pytest.mark.parametrize("args,expected", [
        ("42", 42),
        ("123", 123),
        ("1", 1),
        ("#42", 42),
        ("#123", 123),
    ])
    def test_numeric_arg_extracted(self, args, expected):
        result = parse_pr_argument(args)
        assert result == {"type": "pr_number", "number": expected}

    def test_numeric_with_whitespace(self):
        result = parse_pr_argument("  42  ")
        assert result == {"type": "pr_number", "number": 42}


class TestAutoDetect:
    """Test that missing or non-numeric args fall back to branch auto-detection."""

    def test_empty_string(self):
        assert parse_pr_argument("") == {"type": "detect"}

    def test_whitespace_only(self):
        assert parse_pr_argument("   ") == {"type": "detect"}

    def test_none(self):
        assert parse_pr_argument(None) == {"type": "detect"}

    @pytest.mark.parametrize("args", ["main", "fix-auth-bug", "my-feature-branch"])
    def test_branch_name_falls_back(self, args):
        """Non-numeric, non-help args fall back to auto-detect from branch."""
        assert parse_pr_argument(args) == {"type": "detect"}


class TestHelpRouting:
    """Test that help args are routed to the help type per SKILL.md Step 1."""

    @pytest.mark.parametrize("args", ["help", "--help", "-h", "?"])
    def test_help_triggers_routed(self, args):
        result = parse_pr_argument(args)
        assert result == {"type": "help"}
