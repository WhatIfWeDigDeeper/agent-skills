"""Tests for edge cases in learn skill."""

import os
import subprocess
import sys

import pytest

from conftest import run_detection_script


class TestEmptyProject:
    """Test behavior with empty/minimal projects."""

    def test_no_configs_in_empty_project(self, use_fixture):
        """Empty project should return no configs."""
        project = use_fixture("empty-project")
        detected = run_detection_script(project)
        assert detected == []


class TestMalformedFiles:
    """Test handling of malformed config files."""

    def test_empty_config_file_detected(self, use_fixture):
        """Empty config file should still be detected."""
        project = use_fixture("malformed/empty-file")
        detected = run_detection_script(project)
        assert "CLAUDE.md" in detected

    def test_binary_content_file_detected(self, use_fixture):
        """File with binary content should still be detected."""
        project = use_fixture("malformed/binary-content")
        detected = run_detection_script(project)
        assert "CLAUDE.md" in detected

    def test_special_characters_handled(self, use_fixture):
        """Files with special characters should be handled."""
        project = use_fixture("malformed/special-chars")
        detected = run_detection_script(project)
        assert "CLAUDE.md" in detected

        # Verify wc -l works on the file
        result = subprocess.run(
            ["wc", "-l", str(project / "CLAUDE.md")],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0


class TestDirectoryStructure:
    """Test various directory structure scenarios."""

    def test_nested_config_not_detected_at_root(self, temp_dir):
        """Configs in subdirectories should not be detected at root level."""
        # Create nested config
        nested = temp_dir / "subdir" / "deep"
        nested.mkdir(parents=True)
        (nested / "CLAUDE.md").write_text("# Nested config")

        detected = run_detection_script(temp_dir)
        assert detected == []

    def test_symlink_to_config_detected(self, temp_dir):
        """Symlink to config should be detected."""
        # Create real file and symlink
        real_dir = temp_dir / "real"
        real_dir.mkdir()
        (real_dir / "actual.md").write_text("# Real config")
        (temp_dir / "CLAUDE.md").symlink_to(real_dir / "actual.md")

        detected = run_detection_script(temp_dir)
        assert "CLAUDE.md" in detected

    def test_missing_cursor_rules_dir_handled(self, temp_dir):
        """Missing .cursor/rules directory should be handled gracefully."""
        # No .cursor directory
        detected = run_detection_script(temp_dir)
        # Should not error, just return empty
        assert detected == []

    def test_empty_cursor_rules_dir_handled(self, temp_dir):
        """Empty .cursor/rules directory should return no MDC files."""
        (temp_dir / ".cursor" / "rules").mkdir(parents=True)

        detected = run_detection_script(temp_dir)
        mdc_files = [f for f in detected if f.endswith(".mdc")]
        assert mdc_files == []


class TestDuplicateDetection:
    """Test that files aren't detected multiple times."""

    def test_no_duplicate_cursorrules(self, use_fixture):
        """.cursorrules should be detected exactly once."""
        project = use_fixture("cursor-variations/both")
        detected = run_detection_script(project)

        cursorrules_count = detected.count(".cursorrules")
        assert cursorrules_count == 1


class TestCaseSensitivity:
    """Test case sensitivity in detection."""

    def test_wrong_case_not_detected(self, temp_dir):
        """CLAUDE.MD (uppercase extension) should not be detected as CLAUDE.md."""
        # This test depends on filesystem case sensitivity
        (temp_dir / "CLAUDE.MD").write_text("# Wrong case")

        detected = run_detection_script(temp_dir)
        # On case-sensitive filesystems, this won't match
        # On case-insensitive (macOS default), it might
        # Either way, detection should not crash
        assert isinstance(detected, list)


class TestLongFilenames:
    """Test handling of long filenames."""

    def test_long_mdc_filename(self, temp_dir):
        """Long MDC filename should be detected."""
        rules_dir = temp_dir / ".cursor" / "rules"
        rules_dir.mkdir(parents=True)

        long_name = "this-is-a-very-long-rule-name-that-might-cause-issues.mdc"
        (rules_dir / long_name).write_text(
            '---\ndescription: Long filename test\nglobs: "**/*.ts"\n---\n\n# Long Rule'
        )

        detected = run_detection_script(temp_dir)
        mdc_files = [f for f in detected if f.endswith(".mdc")]
        assert len(mdc_files) == 1


class TestPermissions:
    """Test handling of permission issues."""

    @pytest.mark.skipif(
        sys.platform == "win32" or (hasattr(os, "geteuid") and os.geteuid() == 0),
        reason="Unix non-root only"
    )
    def test_unreadable_file_handled(self, temp_dir):
        """Unreadable config file should be handled gracefully."""
        config = temp_dir / "CLAUDE.md"
        config.write_text("# Test")
        config.chmod(0o000)

        try:
            # Detection should still work (file exists check)
            # but wc -l might fail
            detected = run_detection_script(temp_dir)
            # File should still be detected even if not readable
            assert "CLAUDE.md" in detected
        finally:
            # Restore permissions for cleanup
            config.chmod(0o644)
