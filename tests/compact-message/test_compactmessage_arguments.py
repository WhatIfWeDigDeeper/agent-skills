"""Argument routing for the compact-message skill.

Help triggers route to references/options.md; any other non-empty text is
focus guidance passed through trimmed; empty arguments mean full inference.
"""

import pytest

from conftest import focus_text, is_help_request


class TestHelpTriggers:
    @pytest.mark.parametrize("args", ["help", "--help", "-h", "?"])
    def test_exact_triggers(self, args):
        assert is_help_request(args) is True

    @pytest.mark.parametrize("args", ["HELP", "Help", "--HELP", "-H"])
    def test_case_insensitive(self, args):
        assert is_help_request(args) is True

    @pytest.mark.parametrize("args", ["  help", "help  ", "\t-h\n", " ? "])
    def test_whitespace_trimmed(self, args):
        assert is_help_request(args) is True


class TestNonHelpArguments:
    @pytest.mark.parametrize("args", ["help me", "-help", "??", "keep the help text"])
    def test_non_trigger_text_is_not_help(self, args):
        assert is_help_request(args) is False

    def test_empty_string(self):
        assert is_help_request("") is False

    def test_whitespace_only(self):
        assert is_help_request("   ") is False


class TestFocusText:
    def test_focus_text_passthrough(self):
        args = "keep the eval results, drop the CI debugging"
        assert focus_text(args) == args

    def test_focus_text_is_trimmed(self):
        assert focus_text("  keep PR 253  ") == "keep PR 253"

    def test_help_me_is_focus_text(self):
        assert focus_text("help me") == "help me"

    @pytest.mark.parametrize("args", ["help", "--help", "-h", "?", " HELP "])
    def test_help_has_no_focus_text(self, args):
        assert focus_text(args) is None

    @pytest.mark.parametrize("args", ["", "   ", "\n"])
    def test_empty_has_no_focus_text(self, args):
        assert focus_text(args) is None
