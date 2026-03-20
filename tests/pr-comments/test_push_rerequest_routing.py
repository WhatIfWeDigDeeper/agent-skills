"""Tests for Step 13 push+re-request reviewer list logic in pr-comments skill."""

from conftest import extract_coauthors


def build_reviewer_list(implemented_comments: list[dict], declined_comments: list[dict]) -> list[str]:
    """Build deduplicated reviewer list for push+re-request step.

    Per SKILL.md Step 13: collect all commenters whose feedback was processed
    (implemented, accepted, or declined — anyone replied to or credited).
    """
    all_comments = implemented_comments + declined_comments
    return extract_coauthors(all_comments)


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
