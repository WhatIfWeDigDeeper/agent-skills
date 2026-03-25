"""
Tests for bot poll routing logic:
- Step 13: Poll offered only when bot reviewers were re-requested
- Step 6c: Repoll gate triggers on all-skip with pending bots
"""

from conftest import (
    is_bot_login,
    should_exit_auto_loop,
    should_offer_poll,
    should_repoll_on_all_skip,
    split_human_bot,
)


class TestShouldOfferPoll:
    def test_offers_poll_when_bot_rerequested(self):
        assert should_offer_poll(["copilot-pull-request-reviewer[bot]"]) is True

    def test_offers_poll_for_any_bot(self):
        assert should_offer_poll(["some-other-bot[bot]"]) is True

    def test_no_poll_for_empty_list(self):
        assert should_offer_poll([]) is False

    def test_no_poll_for_human_only(self):
        # Poll is not offered for human-only re-requests
        _, bots = split_human_bot(["alice", "bob"])
        assert should_offer_poll(bots) is False

    def test_offers_poll_mixed_human_and_bot(self):
        _, bots = split_human_bot(["alice", "copilot-pull-request-reviewer[bot]"])
        assert should_offer_poll(bots) is True


class TestIsBotLogin:
    def test_copilot_bot(self):
        assert is_bot_login("copilot-pull-request-reviewer[bot]") is True

    def test_claude_bot(self):
        assert is_bot_login("claude[bot]") is True

    def test_human_login(self):
        assert is_bot_login("alice") is False

    def test_human_login_with_bot_in_name(self):
        # A human whose username happens to contain 'bot' but not as suffix
        assert is_bot_login("robotics-fan") is False

    def test_empty_string(self):
        assert is_bot_login("") is False


class TestSplitHumanBot:
    def test_all_humans(self):
        humans, bots = split_human_bot(["alice", "bob"])
        assert humans == ["alice", "bob"]
        assert bots == []

    def test_all_bots(self):
        humans, bots = split_human_bot(["copilot-pull-request-reviewer[bot]", "claude[bot]"])
        assert humans == []
        assert set(bots) == {"copilot-pull-request-reviewer[bot]", "claude[bot]"}

    def test_mixed(self):
        humans, bots = split_human_bot(["alice", "copilot-pull-request-reviewer[bot]", "bob"])
        assert set(humans) == {"alice", "bob"}
        assert bots == ["copilot-pull-request-reviewer[bot]"]

    def test_empty(self):
        humans, bots = split_human_bot([])
        assert humans == []
        assert bots == []


class TestAutoLoopExitConditions:
    """Test should_exit_auto_loop per SKILL.md Step 13 exit conditions."""

    def test_exit_when_no_new_threads(self):
        """Loop exits when no new unresolved bot threads are found after poll."""
        assert should_exit_auto_loop(iteration=1, max_iterations=10, new_threads=0) is True

    def test_continue_when_threads_remain(self):
        """Loop continues when there are new threads and iterations remain."""
        assert should_exit_auto_loop(iteration=1, max_iterations=10, new_threads=3) is False

    def test_exit_at_max_iterations(self):
        """Loop exits when iteration count reaches the maximum."""
        assert should_exit_auto_loop(iteration=10, max_iterations=10, new_threads=2) is True

    def test_exit_beyond_max_iterations(self):
        """Loop exits if somehow past the maximum."""
        assert should_exit_auto_loop(iteration=11, max_iterations=10, new_threads=2) is True

    def test_continue_below_max_with_threads(self):
        """Loop continues when below max and threads are present."""
        assert should_exit_auto_loop(iteration=3, max_iterations=5, new_threads=1) is False

    def test_exit_at_max_with_no_threads(self):
        """Both conditions true — still exits."""
        assert should_exit_auto_loop(iteration=10, max_iterations=10, new_threads=0) is True

    def test_single_iteration_cap(self):
        """Max iterations of 1 means loop exits after first iteration regardless of threads."""
        assert should_exit_auto_loop(iteration=1, max_iterations=1, new_threads=5) is True

    def test_first_iteration_continues_when_threads_present(self):
        """First iteration does not trigger exit when threads are present and max not reached."""
        assert should_exit_auto_loop(iteration=1, max_iterations=10, new_threads=2) is False

    def test_no_threads_but_bots_remaining_continues(self):
        """No new threads but polled bots haven't responded yet — continue polling."""
        assert should_exit_auto_loop(iteration=1, max_iterations=10, new_threads=0, polled_bots_remaining=1) is False

    def test_no_threads_no_bots_remaining_exits(self):
        """No new threads and all bots have responded — exit."""
        assert should_exit_auto_loop(iteration=1, max_iterations=10, new_threads=0, polled_bots_remaining=0) is True

    def test_max_iterations_overrides_bots_remaining(self):
        """Max iterations exits even if bots are still outstanding."""
        assert should_exit_auto_loop(iteration=10, max_iterations=10, new_threads=0, polled_bots_remaining=2) is True


class TestRepollGate:
    """Test Step 6c repoll gate: all-skip with pending bot reviewers."""

    def test_all_skip_with_pending_bot_triggers_repoll(self):
        """All items skip + pending bot → should repoll."""
        plan = [{"action": "skip"}, {"action": "skip"}]
        assert should_repoll_on_all_skip(plan, ["copilot-pull-request-reviewer[bot]"]) is True

    def test_all_skip_no_pending_bot_no_repoll(self):
        """All items skip + no pending bots + no recent reviews → exit normally."""
        plan = [{"action": "skip"}, {"action": "skip"}]
        assert should_repoll_on_all_skip(plan, []) is False

    def test_all_skip_bot_reviewed_after_fetch(self):
        """All items skip + bot submitted review after fetch_timestamp → should repoll."""
        plan = [{"action": "skip"}]
        recent_review = [{"author": "some-bot[bot]", "submitted_at": "2026-03-25T12:00:01Z"}]
        assert should_repoll_on_all_skip(plan, [], bot_reviews_after_fetch=recent_review) is True

    def test_mixed_actions_no_repoll(self):
        """Some actionable items (fix) + pending bot → no repoll (normal flow)."""
        plan = [{"action": "fix"}, {"action": "skip"}]
        assert should_repoll_on_all_skip(plan, ["copilot-pull-request-reviewer[bot]"]) is False

    def test_empty_plan_with_pending_bot(self):
        """Empty plan + pending bot → should repoll."""
        assert should_repoll_on_all_skip([], ["some-bot[bot]"]) is True

    def test_empty_plan_no_bots(self):
        """Empty plan + no bots → no repoll."""
        assert should_repoll_on_all_skip([], []) is False

    def test_decline_action_prevents_repoll(self):
        """A decline item makes the plan actionable — no repoll."""
        plan = [{"action": "skip"}, {"action": "decline"}]
        assert should_repoll_on_all_skip(plan, ["copilot-pull-request-reviewer[bot]"]) is False

    def test_reply_action_prevents_repoll(self):
        """A reply item makes the plan actionable — no repoll."""
        plan = [{"action": "reply"}, {"action": "skip"}]
        assert should_repoll_on_all_skip(plan, ["copilot-pull-request-reviewer[bot]"]) is False

    def test_consistency_action_prevents_repoll(self):
        """A consistency item makes the plan actionable — no repoll."""
        plan = [{"action": "consistency"}]
        assert should_repoll_on_all_skip(plan, ["copilot-pull-request-reviewer[bot]"]) is False

    def test_accept_suggestion_prevents_repoll(self):
        """An accept suggestion item makes the plan actionable — no repoll."""
        plan = [{"action": "accept suggestion"}]
        assert should_repoll_on_all_skip(plan, ["copilot-pull-request-reviewer[bot]"]) is False

    def test_both_pending_and_recent_review(self):
        """Both pending bots and recent review — should repoll."""
        plan = [{"action": "skip"}]
        recent = [{"author": "bot-a[bot]"}]
        assert should_repoll_on_all_skip(plan, ["bot-b[bot]"], bot_reviews_after_fetch=recent) is True

    def test_unknown_action_prevents_repoll(self):
        """Unknown action value is not treated as skip — no repoll."""
        plan = [{"action": "skip"}, {"action": "unknown"}]
        assert should_repoll_on_all_skip(plan, ["copilot-pull-request-reviewer[bot]"]) is False

    def test_missing_action_prevents_repoll(self):
        """Item with no action key is not treated as skip — no repoll."""
        plan = [{"action": "skip"}, {"some_field": "value"}]
        assert should_repoll_on_all_skip(plan, ["copilot-pull-request-reviewer[bot]"]) is False
