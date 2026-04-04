"""Tests for help trigger detection in peer-review skill."""

import pytest

from conftest import is_help_request


class TestHelpTriggers:
    """Test help trigger detection per SKILL.md."""

    def test_help(self):
        assert is_help_request("help") is True

    def test_double_dash_help(self):
        assert is_help_request("--help") is True

    def test_dash_h(self):
        assert is_help_request("-h") is True

    def test_question_mark(self):
        assert is_help_request("?") is True

    def test_help_case_insensitive(self):
        assert is_help_request("HELP") is True

    def test_help_with_whitespace(self):
        assert is_help_request("  help  ") is True

    def test_empty_string_is_not_help(self):
        assert is_help_request("") is False

    def test_none_is_not_help(self):
        assert is_help_request(None) is False

    def test_help_with_trailing_args_is_not_help(self):
        """'help --staged' is not a pure help trigger."""
        assert is_help_request("help --staged") is False

    def test_staged_is_not_help(self):
        assert is_help_request("--staged") is False

    def test_path_is_not_help(self):
        assert is_help_request("specs/16-peer-review") is False
