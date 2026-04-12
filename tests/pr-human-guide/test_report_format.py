"""Tests for terminal report format in pr-human-guide skill."""

import pytest

from conftest import format_terminal_report

PR_URL = "https://github.com/owner/repo/pull/42"


class TestReportAction:
    """Test 'added to' vs 'updated on' language per SKILL.md Step 6."""

    def test_new_guide_says_added_to(self):
        report = format_terminal_report(42, "Add JWT auth", PR_URL, 1, 1, was_updated=False)
        assert "added to PR #42" in report

    def test_rerun_says_updated_on(self):
        report = format_terminal_report(42, "Add JWT auth", PR_URL, 1, 1, was_updated=True)
        assert "updated on PR #42" in report

    def test_title_included_in_report(self):
        report = format_terminal_report(42, "Add JWT auth", PR_URL, 1, 1, was_updated=False)
        assert "Add JWT auth" in report

    def test_pr_number_included(self):
        report = format_terminal_report(99, "Fix bug", PR_URL, 1, 1, was_updated=True)
        assert "#99" in report


class TestReportURL:
    """Test that the PR URL is always the last line per SKILL.md Step 6."""

    def test_url_is_last_line(self):
        report = format_terminal_report(42, "Title", PR_URL, 1, 1, was_updated=False)
        assert report.splitlines()[-1] == PR_URL

    def test_url_last_line_on_rerun(self):
        report = format_terminal_report(42, "Title", PR_URL, 2, 1, was_updated=True)
        assert report.splitlines()[-1] == PR_URL

    def test_url_last_line_for_zero_items(self):
        report = format_terminal_report(42, "Title", PR_URL, 0, 0, was_updated=False)
        assert report.splitlines()[-1] == PR_URL


class TestItemCountLine:
    """Test item/category count line per SKILL.md Step 6."""

    def test_count_line_present_for_nonzero_items(self):
        report = format_terminal_report(42, "Title", PR_URL, 3, 2, was_updated=False)
        assert "3 item(s) across 2" in report

    def test_single_item_included(self):
        report = format_terminal_report(42, "Title", PR_URL, 1, 1, was_updated=False)
        assert "1 item(s)" in report

    def test_zero_items_suppresses_count_line(self):
        """When no areas are flagged the count line is omitted per SKILL.md Step 6."""
        report = format_terminal_report(42, "Title", PR_URL, 0, 0, was_updated=False)
        assert "item(s)" not in report
        assert "category" not in report

    def test_zero_items_still_has_action_and_url(self):
        report = format_terminal_report(42, "No-op PR", PR_URL, 0, 0, was_updated=False)
        assert "added to PR #42" in report
        assert PR_URL in report
