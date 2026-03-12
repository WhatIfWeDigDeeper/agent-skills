"""Tests for argument parsing in ship-it skill."""

import pytest

from conftest import parse_arguments, to_branch_name


class TestDraftKeyword:
    """Test draft keyword extraction per SKILL.md."""

    def test_draft_only(self):
        result = parse_arguments("draft")
        assert result == {"draft": True, "title": None}

    def test_double_dash_draft(self):
        result = parse_arguments("--draft")
        assert result == {"draft": True, "title": None}

    def test_draft_with_title(self):
        result = parse_arguments("draft fix login timeout")
        assert result == {"draft": True, "title": "fix login timeout"}

    def test_double_dash_draft_with_title(self):
        result = parse_arguments("--draft fix login timeout")
        assert result == {"draft": True, "title": "fix login timeout"}

    def test_draft_case_insensitive(self):
        result = parse_arguments("Draft")
        assert result == {"draft": True, "title": None}

    def test_draft_with_whitespace_title(self):
        """Draft followed by only whitespace should have no title."""
        result = parse_arguments("draft   ")
        assert result == {"draft": True, "title": None}


class TestRegularArguments:
    """Test non-draft argument handling."""

    def test_simple_title(self):
        result = parse_arguments("fix login timeout")
        assert result == {"draft": False, "title": "fix login timeout"}

    def test_single_word(self):
        result = parse_arguments("refactor")
        assert result == {"draft": False, "title": "refactor"}

    def test_empty_string(self):
        result = parse_arguments("")
        assert result == {"draft": False, "title": None}

    def test_none(self):
        result = parse_arguments(None)
        assert result == {"draft": False, "title": None}

    def test_whitespace_only(self):
        result = parse_arguments("   ")
        assert result == {"draft": False, "title": None}

    def test_draft_in_middle_not_keyword(self):
        """'draft' in the middle of text is a title, not the draft keyword."""
        result = parse_arguments("update draft docs")
        assert result == {"draft": False, "title": "update draft docs"}


class TestBranchNaming:
    """Test branch name generation per SKILL.md Step 2."""

    def test_simple_kebab_case(self):
        assert to_branch_name("fix login timeout") == "feat/fix-login-timeout"

    def test_with_change_type(self):
        assert to_branch_name("login timeout", "fix") == "fix/login-timeout"

    def test_special_characters_removed(self):
        assert to_branch_name("handle null response!") == "feat/handle-null-response"

    def test_multiple_spaces_collapsed(self):
        assert to_branch_name("fix   the   bug") == "feat/fix-the-bug"

    def test_uppercase_lowered(self):
        assert to_branch_name("Add User Auth") == "feat/add-user-auth"

    @pytest.mark.parametrize("prefix", ["feat", "fix", "refactor", "docs", "chore", "test"])
    def test_valid_prefixes(self, prefix):
        """All documented prefixes should work."""
        result = to_branch_name("some change", prefix)
        assert result.startswith(f"{prefix}/")
