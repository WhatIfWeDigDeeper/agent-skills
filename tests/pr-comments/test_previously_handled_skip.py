"""Tests for the Step 6 previously-handled skip and its edited-after-reply exception.

An unresolved inline thread that already has a reply from the PR author or the
authenticated user was handled in a prior run and is normally skipped. But a
reviewer can edit their comment after that reply to add new feedback; in that
case the thread must be re-planned rather than skipped. The exception is
self-terminating — a fresh reply timestamp is newer than the comment's
``updated_at``, so the thread is skipped again on the next run.
"""

from conftest import is_previously_handled


class TestPreviouslyHandledSkip:
    def test_no_operator_reply_is_not_previously_handled(self):
        """A thread never replied to was not handled in a prior run."""
        assert is_previously_handled("2026-06-01T00:00:00Z", []) is False

    def test_reply_after_comment_with_no_later_edit_is_skipped(self):
        """Operator replied and the reviewer never edited afterward → skip."""
        assert (
            is_previously_handled(
                "2026-06-01T00:00:00Z",
                ["2026-06-02T00:00:00Z"],
            )
            is True
        )

    def test_edit_after_latest_reply_resurfaces_thread(self):
        """Comment edited after the latest operator reply → re-plan, not skip."""
        assert (
            is_previously_handled(
                "2026-06-03T00:00:00Z",
                ["2026-06-02T00:00:00Z"],
            )
            is False
        )

    def test_edit_before_latest_reply_is_still_skipped(self):
        """An edit older than the reply was already seen → skip."""
        assert (
            is_previously_handled(
                "2026-06-01T00:00:00Z",
                ["2026-06-01T00:00:00Z", "2026-06-02T00:00:00Z"],
            )
            is True
        )

    def test_edit_equal_to_latest_reply_is_skipped(self):
        """Equal timestamps are not 'newer' → skip (boundary)."""
        assert (
            is_previously_handled(
                "2026-06-02T00:00:00Z",
                ["2026-06-02T00:00:00Z"],
            )
            is True
        )

    def test_missing_updated_at_falls_back_to_skip(self):
        """Unknown edit time cannot prove a newer edit → skip as handled."""
        assert is_previously_handled("", ["2026-06-02T00:00:00Z"]) is True

    def test_latest_of_multiple_replies_is_used(self):
        """The comparison uses the most recent operator reply, not the first."""
        # Edited after the first reply but before the second → already seen → skip.
        assert (
            is_previously_handled(
                "2026-06-02T12:00:00Z",
                ["2026-06-02T00:00:00Z", "2026-06-03T00:00:00Z"],
            )
            is True
        )
