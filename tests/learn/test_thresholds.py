"""Tests for size threshold logic in learn skill."""

import pytest

from conftest import classify_size, get_line_count


class TestSizeClassification:
    """Test the size classification logic from SKILL.md."""

    def test_healthy_under_400_lines(self, use_fixture):
        """Files under 400 lines should be classified as healthy."""
        project = use_fixture("size-variations/healthy")
        lines = get_line_count(project / "CLAUDE.md")
        assert lines < 400
        assert classify_size(lines) == "healthy"

    def test_warning_400_to_500_lines(self, use_fixture):
        """Files with 400-500 lines should be classified as warning."""
        project = use_fixture("size-variations/warning")
        lines = get_line_count(project / "CLAUDE.md")
        assert 400 <= lines <= 500
        assert classify_size(lines) == "warning"

    def test_oversized_over_500_lines(self, use_fixture):
        """Files over 500 lines should be classified as oversized."""
        project = use_fixture("size-variations/oversized")
        lines = get_line_count(project / "CLAUDE.md")
        assert lines > 500
        assert classify_size(lines) == "oversized"


class TestBoundaryConditions:
    """Test exact boundary values."""

    def test_exactly_400_lines_is_warning(self, use_fixture):
        """Exactly 400 lines should be in warning zone."""
        project = use_fixture("size-variations/at-400")
        lines = get_line_count(project / "CLAUDE.md")
        # Allow some tolerance for generation variance
        assert 395 <= lines <= 405
        assert classify_size(400) == "warning"

    def test_exactly_500_lines_is_warning(self, use_fixture):
        """Exactly 500 lines should still be warning (not oversized)."""
        project = use_fixture("size-variations/at-500")
        lines = get_line_count(project / "CLAUDE.md")
        # Allow some tolerance for generation variance
        assert 495 <= lines <= 505
        assert classify_size(500) == "warning"

    def test_399_lines_is_healthy(self):
        """399 lines should be healthy."""
        assert classify_size(399) == "healthy"

    def test_501_lines_is_oversized(self):
        """501 lines should be oversized."""
        assert classify_size(501) == "oversized"


class TestEdgeCases:
    """Test edge cases for size classification."""

    def test_empty_file_is_healthy(self, use_fixture):
        """Empty file (0 lines) should be healthy."""
        project = use_fixture("malformed/empty-file")
        lines = get_line_count(project / "CLAUDE.md")
        assert lines == 0
        assert classify_size(lines) == "healthy"

    def test_single_line_is_healthy(self):
        """Single line file should be healthy."""
        assert classify_size(1) == "healthy"

    @pytest.mark.parametrize(
        "lines,expected",
        [
            (0, "healthy"),
            (100, "healthy"),
            (399, "healthy"),
            (400, "warning"),
            (450, "warning"),
            (500, "warning"),
            (501, "oversized"),
            (1000, "oversized"),
        ],
    )
    def test_classification_ranges(self, lines: int, expected: str):
        """Test classification across the full range of values."""
        assert classify_size(lines) == expected
