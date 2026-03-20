"""Tests for Step 13 push+re-request reviewer list logic in pr-comments skill."""

from conftest import build_reviewer_list


class TestReviewerListDeduplication:
    """Test Step 13 reviewer-list deduplication per SKILL.md."""

    def test_implemented_only(self):
        implemented = [{"author": "alice"}, {"author": "bob"}]
        result = build_reviewer_list(implemented, [])
        assert result == ["alice", "bob"]

    def test_declined_only(self):
        declined = [{"author": "carol"}]
        result = build_reviewer_list([], declined)
        assert result == ["carol"]

    def test_combined_implemented_and_declined(self):
        """Declined commenters are included alongside implemented ones."""
        implemented = [{"author": "alice"}, {"author": "bob"}]
        declined = [{"author": "carol"}]
        result = build_reviewer_list(implemented, declined)
        assert result == ["alice", "bob", "carol"]

    def test_same_author_in_both_lists(self):
        """Author who both had an implemented comment and a declined comment appears once."""
        implemented = [{"author": "alice"}]
        declined = [{"author": "alice"}]
        result = build_reviewer_list(implemented, declined)
        assert result == ["alice"]

    def test_multiple_comments_same_author(self):
        """Author with multiple implemented comments appears only once."""
        implemented = [{"author": "alice"}, {"author": "alice"}, {"author": "bob"}]
        declined = [{"author": "bob"}]
        result = build_reviewer_list(implemented, declined)
        assert result == ["alice", "bob"]

    def test_empty_inputs(self):
        assert build_reviewer_list([], []) == []

    def test_declined_commenter_not_omitted(self):
        """SKILL.md Step 13: declined commenters must appear in re-request list."""
        implemented = [{"author": "alice"}]
        declined = [{"author": "eve"}]
        result = build_reviewer_list(implemented, declined)
        assert "eve" in result

    def test_sorted_output(self):
        implemented = [{"author": "charlie"}, {"author": "alice"}]
        declined = [{"author": "bob"}]
        result = build_reviewer_list(implemented, declined)
        assert result == ["alice", "bob", "charlie"]

    def test_replied_only(self):
        """Commenters answered via reply action appear in re-request list."""
        replied = [{"author": "diana"}]
        result = build_reviewer_list([], [], replied_comments=replied)
        assert result == ["diana"]

    def test_replied_combined_with_implemented_and_declined(self):
        """All three Step 13 sources contribute to the reviewer list."""
        implemented = [{"author": "alice"}]
        declined = [{"author": "bob"}]
        replied = [{"author": "carol"}]
        result = build_reviewer_list(implemented, declined, replied_comments=replied)
        assert result == ["alice", "bob", "carol"]

    def test_replied_deduplication_across_sources(self):
        """Author appearing in both replied and implemented lists appears only once."""
        implemented = [{"author": "alice"}]
        replied = [{"author": "alice"}, {"author": "bob"}]
        result = build_reviewer_list(implemented, [], replied_comments=replied)
        assert result == ["alice", "bob"]

    def test_replied_defaults_to_empty(self):
        """Omitting replied_comments works the same as passing an empty list."""
        implemented = [{"author": "alice"}]
        assert build_reviewer_list(implemented, []) == build_reviewer_list(implemented, [], replied_comments=[])
