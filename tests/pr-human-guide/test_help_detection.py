"""Tests for help trigger detection in pr-human-guide skill."""

import pytest

from conftest import is_help_request


class TestHelpTriggers:
    """Test that documented help arguments are correctly identified per SKILL.md Step 1."""

    @pytest.mark.parametrize("args", ["help", "--help", "-h", "?"])
    def test_recognized_help_triggers(self, args):
        assert is_help_request(args) is True

    @pytest.mark.parametrize("args", ["Help", "HELP", "--HELP", "-H"])
    def test_case_insensitive(self, args):
        assert is_help_request(args) is True

    @pytest.mark.parametrize("args", [" help ", " --help\t", "\t-h "])
    def test_whitespace_trimmed(self, args):
        assert is_help_request(args) is True


class TestNonHelpArguments:
    """Test that non-help arguments are not mistakenly detected as help."""

    @pytest.mark.parametrize("args", ["42", "123", "help me", "-help", "??", "0", "#42"])
    def test_normal_args_not_help(self, args):
        assert is_help_request(args) is False

    def test_empty_string(self):
        assert is_help_request("") is False

    def test_whitespace_only(self):
        assert is_help_request("   ") is False
