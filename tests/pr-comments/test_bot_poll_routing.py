"""
Tests for Step 13 bot poll routing logic:
- Poll offered only when bot reviewers were re-requested
- Poll not offered for human-only re-requests
- Poll not offered when reviewer list is empty
"""

import pytest

from conftest import is_bot_login, should_offer_poll, split_human_bot


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
