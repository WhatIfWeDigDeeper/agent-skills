"""Tests for help trigger detection in pr-comments skill."""

import pytest

from conftest import is_help_request


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
        "42",
        "123",
        "help me",
        "-help",
        "??",
        "0",
    ])
    def test_normal_args_not_help(self, args):
        """Normal pr-comments arguments should not trigger help."""
        assert is_help_request(args) is False

    def test_empty_string(self):
        assert is_help_request("") is False

    def test_whitespace_only(self):
        assert is_help_request("   ") is False
