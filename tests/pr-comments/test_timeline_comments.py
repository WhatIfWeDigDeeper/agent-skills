"""
Tests for PR timeline comment handling (Step 2c):
- Filtering: exclude PR author, exclude authenticated user
- Dedup: 200-char non-whitespace prefix match against review body comments
- Already-addressed detection: @mention or quote linkage required
- Signal 3 bot polling: timeline-only bot response triggers loop-back
- All-skip repoll gate: post-fetch bot timeline comment triggers re-fetch
"""

from conftest import (
    filter_timeline_comments,
    is_already_addressed,
    should_repoll_on_all_skip,
    should_signal3_fire,
)


class TestFilterTimelineComments:
    def _make_tc(self, author: str, body: str = "feedback", created_at: str = "2026-01-01T00:00:00Z") -> dict:
        return {"id": 1, "author": author, "body": body, "created_at": created_at}

    def test_excludes_pr_author(self):
        comments = [self._make_tc("alice"), self._make_tc("bob")]
        result = filter_timeline_comments(comments, pr_author="alice", auth_user="bot", review_body_comments=[])
        assert len(result) == 1
        assert result[0]["author"] == "bob"

    def test_excludes_authenticated_user(self):
        comments = [self._make_tc("alice"), self._make_tc("skillbot")]
        result = filter_timeline_comments(comments, pr_author="owner", auth_user="skillbot", review_body_comments=[])
        assert len(result) == 1
        assert result[0]["author"] == "alice"

    def test_excludes_both_pr_author_and_auth_user(self):
        comments = [
            self._make_tc("prauthor"),
            self._make_tc("skillbot"),
            self._make_tc("reviewer"),
        ]
        result = filter_timeline_comments(comments, pr_author="prauthor", auth_user="skillbot", review_body_comments=[])
        assert len(result) == 1
        assert result[0]["author"] == "reviewer"

    def test_keeps_unrelated_comments(self):
        comments = [self._make_tc("alice"), self._make_tc("bob"), self._make_tc("carol")]
        result = filter_timeline_comments(comments, pr_author="owner", auth_user="skillbot", review_body_comments=[])
        assert len(result) == 3

    def test_dedup_removes_identical_body_same_author(self):
        """Timeline comment with same author and body as review body is removed."""
        body = "This function has a potential null pointer dereference."
        tc = self._make_tc("copilot[bot]", body=body)
        rb = {"author": "copilot[bot]", "body": body, "id": 99}
        result = filter_timeline_comments([tc], pr_author="owner", auth_user="bot", review_body_comments=[rb])
        assert result == []

    def test_dedup_keeps_different_content_same_author(self):
        """Timeline comment with same author but different content is kept."""
        rb = {"author": "copilot[bot]", "body": "General summary of changes.", "id": 99}
        tc = self._make_tc("copilot[bot]", body="This function has a potential null pointer dereference.")
        result = filter_timeline_comments([tc], pr_author="owner", auth_user="bot", review_body_comments=[rb])
        assert len(result) == 1

    def test_dedup_requires_same_author(self):
        """Identical body from different author is NOT deduped."""
        body = "Please fix the null check."
        rb = {"author": "alice", "body": body, "id": 99}
        tc = self._make_tc("bob", body=body)
        result = filter_timeline_comments([tc], pr_author="owner", auth_user="bot", review_body_comments=[rb])
        assert len(result) == 1

    def test_dedup_matches_on_200_nonwhitespace_prefix(self):
        """Dedup uses first 200 non-whitespace characters; whitespace differences don't affect it."""
        base = "a" * 200
        body_with_spaces = " ".join(base)  # spaces inserted between chars
        rb = {"author": "copilot[bot]", "body": base, "id": 99}
        tc = self._make_tc("copilot[bot]", body=body_with_spaces)
        # Both have the same 200 non-whitespace chars → dedup fires
        result = filter_timeline_comments([tc], pr_author="owner", auth_user="bot", review_body_comments=[rb])
        assert result == []

    def test_dedup_does_not_fire_when_prefix_differs(self):
        """Bodies that differ within first 200 non-whitespace chars are NOT deduped."""
        rb = {"author": "copilot[bot]", "body": "short review comment", "id": 99}
        tc = self._make_tc("copilot[bot]", body="completely different timeline comment")
        result = filter_timeline_comments([tc], pr_author="owner", auth_user="bot", review_body_comments=[rb])
        assert len(result) == 1

    def test_empty_input(self):
        assert filter_timeline_comments([], pr_author="owner", auth_user="bot", review_body_comments=[]) == []


class TestIsAlreadyAddressed:
    def _make_comment(self, author: str, body: str, created_at: str) -> dict:
        return {"author": author, "body": body, "created_at": created_at}

    def test_mention_in_later_pr_author_comment(self):
        """PR author later comment with @mention counts as addressed."""
        comment = self._make_comment("alice", "This looks wrong.", "2026-01-01T10:00:00Z")
        later = self._make_comment("prowner", "Thanks @alice, fixed in the latest commit.", "2026-01-01T11:00:00Z")
        assert is_already_addressed(comment, [comment, later], pr_author="prowner", auth_user="skillbot") is True

    def test_quote_in_later_pr_author_comment(self):
        """PR author later comment with blockquote counts as addressed."""
        comment = self._make_comment("alice", "This looks wrong.", "2026-01-01T10:00:00Z")
        later = self._make_comment("prowner", "> This looks wrong.\nYep, fixed.", "2026-01-01T11:00:00Z")
        assert is_already_addressed(comment, [comment, later], pr_author="prowner", auth_user="skillbot") is True

    def test_mention_in_later_auth_user_comment(self):
        """Authenticated user later comment with @mention counts as addressed."""
        comment = self._make_comment("alice", "Please add tests.", "2026-01-01T10:00:00Z")
        later = self._make_comment("skillbot", "@alice tests added, see latest commit.", "2026-01-01T11:00:00Z")
        assert is_already_addressed(comment, [comment, later], pr_author="prowner", auth_user="skillbot") is True

    def test_plain_later_comment_does_not_count(self):
        """An unrelated follow-up from PR author without mention or quote does NOT count."""
        comment = self._make_comment("alice", "This looks wrong.", "2026-01-01T10:00:00Z")
        # PR author posts an unrelated follow-up, no mention of alice
        later = self._make_comment("prowner", "Updated the README as well.", "2026-01-01T11:00:00Z")
        assert is_already_addressed(comment, [comment, later], pr_author="prowner", auth_user="skillbot") is False

    def test_earlier_pr_author_comment_does_not_count(self):
        """A comment before the reviewer's comment does not count as addressing it."""
        pr_author_comment = self._make_comment("prowner", "@alice thanks for the feedback.", "2026-01-01T09:00:00Z")
        alice_comment = self._make_comment("alice", "This looks wrong.", "2026-01-01T10:00:00Z")
        assert is_already_addressed(alice_comment, [pr_author_comment, alice_comment], pr_author="prowner", auth_user="skillbot") is False

    def test_no_later_comments(self):
        """No later comments → not addressed."""
        comment = self._make_comment("alice", "Please fix this.", "2026-01-01T10:00:00Z")
        assert is_already_addressed(comment, [comment], pr_author="prowner", auth_user="skillbot") is False

    def test_later_comment_from_different_user_does_not_count(self):
        """A later comment from a third-party reviewer doesn't count as addressing."""
        comment = self._make_comment("alice", "This looks wrong.", "2026-01-01T10:00:00Z")
        later = self._make_comment("carol", "@alice good point.", "2026-01-01T11:00:00Z")
        assert is_already_addressed(comment, [comment, later], pr_author="prowner", auth_user="skillbot") is False

    def test_same_timestamp_does_not_count(self):
        """A comment at the same timestamp (not strictly later) does not count."""
        comment = self._make_comment("alice", "Fix this please.", "2026-01-01T10:00:00Z")
        same_time = self._make_comment("prowner", "@alice done", "2026-01-01T10:00:00Z")
        assert is_already_addressed(comment, [comment, same_time], pr_author="prowner", auth_user="skillbot") is False


class TestSignal3:
    def test_fires_when_bot_timeline_comment_present(self):
        new_comments = [{"author": "claude[bot]", "body": "Found an issue.", "created_at": "2026-01-01T12:00:00Z"}]
        assert should_signal3_fire(new_comments) is True

    def test_no_fire_when_empty(self):
        assert should_signal3_fire([]) is False

    def test_fires_for_multiple_comments(self):
        new_comments = [
            {"author": "copilot[bot]", "body": "Suggestion 1", "created_at": "2026-01-01T12:00:00Z"},
            {"author": "copilot[bot]", "body": "Suggestion 2", "created_at": "2026-01-01T12:01:00Z"},
        ]
        assert should_signal3_fire(new_comments) is True


class TestAllSkipRepollWithTimeline:
    """Tests that the all-skip repoll gate fires on post-fetch bot timeline comments."""

    def test_repoll_fires_on_bot_timeline_after_fetch(self):
        """All-skip plan + bot timeline comment after fetch_timestamp → repoll."""
        plan = [{"action": "skip"}]
        timeline = [{"author": "claude[bot]", "body": "Found an issue.", "created_at": "2026-01-01T12:00:00Z"}]
        assert should_repoll_on_all_skip(plan, [], bot_timeline_after_fetch=timeline) is True

    def test_no_repoll_when_only_non_bot_timeline(self):
        """Non-bot timeline comments (already filtered by caller) do not trigger repoll."""
        plan = [{"action": "skip"}]
        # Caller is responsible for only passing bot-authored entries; here we pass nothing
        assert should_repoll_on_all_skip(plan, [], bot_timeline_after_fetch=[]) is False

    def test_repoll_fires_on_combined_pending_and_timeline(self):
        """Both pending bots and bot timeline comment — repoll fires."""
        plan = [{"action": "skip"}]
        timeline = [{"author": "copilot[bot]", "body": "See comment.", "created_at": "2026-01-01T12:00:00Z"}]
        assert should_repoll_on_all_skip(plan, ["some-bot[bot]"], bot_timeline_after_fetch=timeline) is True

    def test_actionable_plan_prevents_repoll_even_with_timeline(self):
        """An actionable plan item prevents repoll even if bot timeline exists."""
        plan = [{"action": "fix"}, {"action": "skip"}]
        timeline = [{"author": "claude[bot]", "body": "Found an issue.", "created_at": "2026-01-01T12:00:00Z"}]
        assert should_repoll_on_all_skip(plan, [], bot_timeline_after_fetch=timeline) is False
