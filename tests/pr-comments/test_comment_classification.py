"""Tests for comment classification in pr-comments skill."""

import pytest

from conftest import classify_comment, extract_suggestion_content, extract_coauthors


class TestClassifyComment:
    """Test comment classification per SKILL.md Steps 2 and 4a."""

    def test_regular_comment(self):
        comment = {"body": "Please rename this variable.", "in_reply_to_id": None}
        assert classify_comment(comment) == "regular"

    def test_suggestion_comment(self):
        comment = {
            "body": "```suggestion\nconst newName = value;\n```",
            "in_reply_to_id": None,
        }
        assert classify_comment(comment) == "suggestion"

    def test_suggestion_with_language_hint(self):
        """Some editors append language hints after suggestion keyword."""
        comment = {
            "body": "```suggestion:javascript\nfixed code\n```",
            "in_reply_to_id": None,
        }
        assert classify_comment(comment) == "suggestion"

    def test_reply_comment(self):
        comment = {"body": "Good point, I'll fix that.", "in_reply_to_id": 123}
        assert classify_comment(comment) == "reply"

    def test_reply_with_suggestion_still_reply(self):
        """Replies are classified by in_reply_to_id, even if body has suggestion."""
        comment = {
            "body": "```suggestion\ncode\n```",
            "in_reply_to_id": 456,
        }
        assert classify_comment(comment) == "reply"

    def test_empty_body(self):
        comment = {"body": "", "in_reply_to_id": None}
        assert classify_comment(comment) == "regular"

    def test_backticks_in_body_not_suggestion(self):
        """Regular code blocks should not be mistaken for suggestions."""
        comment = {
            "body": "Use this pattern:\n```javascript\nconst x = 1;\n```",
            "in_reply_to_id": None,
        }
        assert classify_comment(comment) == "regular"


class TestExtractSuggestion:
    """Test suggestion block extraction per SKILL.md Step 7."""

    def test_simple_suggestion(self):
        body = "Try this:\n```suggestion\nconst x = 1;\n```"
        assert extract_suggestion_content(body) == "const x = 1;\n"

    def test_multiline_suggestion(self):
        body = "```suggestion\nline1\nline2\nline3\n```"
        result = extract_suggestion_content(body)
        assert result == "line1\nline2\nline3\n"

    def test_empty_suggestion(self):
        """Empty suggestion block (delete the lines)."""
        body = "```suggestion\n```"
        result = extract_suggestion_content(body)
        assert result == ""

    def test_no_suggestion_block(self):
        body = "Please fix this variable name."
        assert extract_suggestion_content(body) is None

    def test_regular_code_block_not_extracted(self):
        body = "```javascript\nconst x = 1;\n```"
        assert extract_suggestion_content(body) is None

    def test_suggestion_with_surrounding_text(self):
        body = "Consider this change:\n```suggestion\nfixed();\n```\nThis is better."
        assert extract_suggestion_content(body) == "fixed();\n"


class TestExtractCoauthors:
    """Test co-author extraction per SKILL.md Step 9."""

    def test_single_author(self):
        comments = [{"author": "alice"}]
        assert extract_coauthors(comments) == ["alice"]

    def test_multiple_unique_authors(self):
        comments = [{"author": "alice"}, {"author": "bob"}]
        assert extract_coauthors(comments) == ["alice", "bob"]

    def test_deduplication(self):
        """Same author multiple times should appear once."""
        comments = [
            {"author": "alice"},
            {"author": "bob"},
            {"author": "alice"},
        ]
        assert extract_coauthors(comments) == ["alice", "bob"]

    def test_empty_list(self):
        assert extract_coauthors([]) == []

    def test_empty_author_skipped(self):
        comments = [{"author": ""}, {"author": "alice"}]
        assert extract_coauthors(comments) == ["alice"]

    def test_missing_author_skipped(self):
        comments = [{}, {"author": "alice"}]
        assert extract_coauthors(comments) == ["alice"]

    def test_sorted_output(self):
        comments = [{"author": "charlie"}, {"author": "alice"}, {"author": "bob"}]
        assert extract_coauthors(comments) == ["alice", "bob", "charlie"]
