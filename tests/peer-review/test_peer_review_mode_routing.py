"""Tests for review mode routing in peer-review skill."""

import pytest

from conftest import detect_mode, parse_arguments


class TestModeDetection:
    """Test auto-detection of review mode from target and directory contents."""

    def test_spec_mode_when_both_files_present(self):
        assert detect_mode("specs/16-peer-review", has_plan_md=True, has_tasks_md=True) == "spec"

    def test_consistency_mode_when_only_plan_md(self):
        assert detect_mode("specs/16-peer-review", has_plan_md=True, has_tasks_md=False) == "consistency"

    def test_consistency_mode_when_only_tasks_md(self):
        assert detect_mode("specs/16-peer-review", has_plan_md=False, has_tasks_md=True) == "consistency"

    def test_consistency_mode_when_neither_file(self):
        assert detect_mode("skills/peer-review", has_plan_md=False, has_tasks_md=False) == "consistency"

    def test_consistency_mode_for_single_file_path(self):
        assert detect_mode("skills/peer-review/SKILL.md", has_plan_md=False, has_tasks_md=False) == "consistency"


class TestDiffModeTargets:
    """Staged/branch/PR targets always map to diff mode (not path-based routing)."""

    def test_no_args_is_staged(self):
        result = parse_arguments("")
        assert result["target_type"] == "staged"

    def test_staged_flag_is_staged(self):
        result = parse_arguments("--staged")
        assert result["target_type"] == "staged"

    def test_pr_target(self):
        result = parse_arguments("--pr 85")
        assert result["target_type"] == "pr"

    def test_branch_target(self):
        result = parse_arguments("--branch specs/16-peer-review")
        assert result["target_type"] == "branch"

    def test_path_target_goes_to_path_routing(self):
        """Path targets are further routed to spec or consistency by directory contents."""
        result = parse_arguments("specs/16-peer-review")
        assert result["target_type"] == "path"
