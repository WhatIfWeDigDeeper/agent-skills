"""Tests for Step 9 post-edit drift re-scan in pr-comments skill."""

from conftest import (
    find_drift_rows,
    is_nontrivial_substring,
    requires_manual_confirmation,
)


class TestIsNontrivialSubstring:
    """Test the non-trivial substring filter (Step 9 eligibility)."""

    def test_long_string_is_nontrivial(self):
        assert is_nontrivial_substring("this is a long enough string to qualify") is True

    def test_exactly_20_chars_is_nontrivial(self):
        assert is_nontrivial_substring("a" * 20) is True

    def test_19_chars_not_nontrivial(self):
        assert is_nontrivial_substring("a" * 19) is False

    def test_cli_flag_is_nontrivial(self):
        assert is_nontrivial_substring("--body-file") is True

    def test_cli_flag_short_still_nontrivial(self):
        assert is_nontrivial_substring("--body") is True

    def test_file_path_is_nontrivial(self):
        assert is_nontrivial_substring("skills/pr-comments/SKILL.md") is True

    def test_numeric_only_not_nontrivial(self):
        assert is_nontrivial_substring("42") is False

    def test_empty_string_not_nontrivial(self):
        assert is_nontrivial_substring("") is False

    def test_whitespace_only_not_nontrivial(self):
        assert is_nontrivial_substring("   ") is False

    def test_short_word_not_nontrivial(self):
        assert is_nontrivial_substring("fix") is False


class TestFindDriftRows:
    """Test the drift-match search (Step 9 core logic)."""

    def test_cli_flag_drift_detected(self):
        """A replaced CLI flag appearing in a sibling PR-modified file is flagged."""
        replacements = [("--body", "--body-file")]
        pr_files = {
            "specs/22-pr-human-guide/plan.md": (
                "gh pr edit {pr_number} --body \"$UPDATED_BODY\"\n"
            )
        }
        rows = find_drift_rows(replacements, pr_files)
        assert len(rows) == 1
        assert rows[0]["file"] == "specs/22-pr-human-guide/plan.md"
        assert rows[0]["old"] == "--body"

    def test_long_prose_drift_detected(self):
        """A replaced long prose phrase found in another file is flagged."""
        old = "use judgment to form an appropriate grep/find"
        replacements = [(old, "form an appropriate search")]
        pr_files = {
            "specs/23-test/plan.md": f"The specific search: {old}.\n",
            "README.md": "No match here.\n",
        }
        rows = find_drift_rows(replacements, pr_files)
        assert len(rows) == 1
        assert rows[0]["file"] == "specs/23-test/plan.md"

    def test_no_drift_silent(self):
        """When no PR-modified file references the old substring, no rows are added."""
        replacements = [("--body", "--body-file")]
        pr_files = {
            "README.md": "Some unrelated content here.\n",
            "evals/test/benchmark.json": '{"evidence": "uses --body-file correctly"}\n',
        }
        rows = find_drift_rows(replacements, pr_files)
        assert rows == []

    def test_trivial_substring_excluded(self):
        """Substrings that are too short or common are not scanned."""
        replacements = [("fix", "repair"), ("the", "a"), ("42", "43")]
        pr_files = {
            "README.md": "fix the 42 issues\n",
        }
        rows = find_drift_rows(replacements, pr_files)
        assert rows == []

    def test_multiple_files_multiple_matches(self):
        """Each PR-modified file with the old substring generates its own row."""
        replacements = [("--body", "--body-file")]
        pr_files = {
            "specs/plan.md": "gh pr edit --body \"$X\"\n",
            "evals/benchmark.json": '"evidence": "skill called --body directly"\n',
            "README.md": "No match here.\n",
        }
        rows = find_drift_rows(replacements, pr_files)
        assert len(rows) == 2
        files_flagged = {r["file"] for r in rows}
        assert "specs/plan.md" in files_flagged
        assert "evals/benchmark.json" in files_flagged

    def test_empty_replacements_no_rows(self):
        rows = find_drift_rows([], {"README.md": "content"})
        assert rows == []

    def test_empty_pr_files_no_rows(self):
        rows = find_drift_rows([("--body", "--body-file")], {})
        assert rows == []


class TestStep9ConfirmationBehavior:
    """Step 9 drift rows must NOT trigger manual confirmation (Step 7 escalation)."""

    def test_step9_drift_row_does_not_force_manual(self):
        plan = [{"action": "consistency", "source": "9"}]
        assert requires_manual_confirmation(plan) is False

    def test_step6b_consistency_still_forces_manual(self):
        plan = [{"action": "consistency", "source": "6b"}]
        assert requires_manual_confirmation(plan) is True

    def test_untagged_consistency_defaults_to_6b_behavior(self):
        """Items without source field behave as Step 6b (backward compat)."""
        plan = [{"action": "consistency"}]
        assert requires_manual_confirmation(plan) is True

    def test_mixed_step6b_and_step9_forces_manual_due_to_6b(self):
        """If both present, the Step 6b row triggers escalation."""
        plan = [
            {"action": "consistency", "source": "9"},
            {"action": "consistency", "source": "6b"},
        ]
        assert requires_manual_confirmation(plan) is True

    def test_only_step9_rows_no_force(self):
        plan = [
            {"action": "fix"},
            {"action": "consistency", "source": "9"},
            {"action": "consistency", "source": "9"},
        ]
        assert requires_manual_confirmation(plan) is False
