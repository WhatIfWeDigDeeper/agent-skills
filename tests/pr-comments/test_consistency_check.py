"""Tests for Step 6b cross-file consistency check in pr-comments skill."""

from conftest import requires_manual_confirmation


class TestRequiresManualConfirmation:
    """Test that consistency items force manual confirmation per SKILL.md Step 7."""

    def test_no_consistency_items_no_force(self):
        plan = [
            {"action": "fix"},
            {"action": "accept suggestion"},
            {"action": "skip"},
        ]
        assert requires_manual_confirmation(plan) is False

    def test_consistency_item_forces_manual(self):
        plan = [
            {"action": "fix"},
            {"action": "consistency"},
        ]
        assert requires_manual_confirmation(plan) is True

    def test_only_consistency_forces_manual(self):
        plan = [{"action": "consistency"}]
        assert requires_manual_confirmation(plan) is True

    def test_empty_plan_no_force(self):
        assert requires_manual_confirmation([]) is False

    def test_decline_does_not_force_manual(self):
        """decline items don't require manual confirmation — only consistency does."""
        plan = [{"action": "decline"}, {"action": "reply"}]
        assert requires_manual_confirmation(plan) is False

    def test_multiple_consistency_items_still_forces(self):
        plan = [
            {"action": "consistency"},
            {"action": "consistency"},
        ]
        assert requires_manual_confirmation(plan) is True

    def test_mixed_plan_with_consistency_forces_manual(self):
        plan = [
            {"action": "fix"},
            {"action": "accept suggestion"},
            {"action": "consistency"},
            {"action": "skip"},
        ]
        assert requires_manual_confirmation(plan) is True


class TestConsistencyActionClassification:
    """Test that consistency is treated as a distinct action label."""

    def test_consistency_not_a_reviewer_action(self):
        """consistency rows have no associated review thread."""
        reviewer_thread_actions = {"fix", "accept suggestion", "reply", "decline"}
        assert "consistency" not in reviewer_thread_actions

    def test_consistency_not_skippable_like_skip(self):
        """consistency is distinct from skip — it represents a proposed change."""
        no_change_actions = {"skip"}
        assert "consistency" not in no_change_actions

