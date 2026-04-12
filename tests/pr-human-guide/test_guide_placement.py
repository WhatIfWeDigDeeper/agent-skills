"""Tests for guide append/replace logic in pr-human-guide skill."""

from conftest import (
    CLOSING_MARKER,
    OPENING_MARKER,
    append_guide,
    apply_guide,
    count_occurrences,
    has_existing_guide,
    replace_guide,
)

SAMPLE_GUIDE = (
    f"{OPENING_MARKER}\n"
    "## Review Guide\n\n"
    "> Areas identified by automated analysis as needing human judgment.\n\n"
    "### Security\n"
    "- [`src/auth/middleware.ts`](https://github.com/owner/repo/pull/42/files#diff-abc)"
    " — New token validation logic\n\n"
    f"{CLOSING_MARKER}"
)


class TestHasExistingGuide:
    """Test detection of an existing guide block per SKILL.md Step 5."""

    def test_body_with_both_markers(self):
        body = f"PR description.\n\n{OPENING_MARKER}\n## Review Guide\n{CLOSING_MARKER}"
        assert has_existing_guide(body) is True

    def test_body_without_markers(self):
        assert has_existing_guide("PR description.\n\nNo guide here.") is False

    def test_empty_body(self):
        assert has_existing_guide("") is False

    def test_opening_marker_sufficient_for_detection(self):
        """Detection is based on the opening marker alone (closing may be missing on corrupt body)."""
        body = f"Description.\n{OPENING_MARKER}\n## Review Guide"
        assert has_existing_guide(body) is True


class TestAppendGuide:
    """Test appending a guide to a body with no existing markers per SKILL.md Step 5."""

    def test_guide_appended_to_existing_body(self):
        result = append_guide("This PR adds a new feature.", SAMPLE_GUIDE)
        assert "This PR adds a new feature." in result
        assert OPENING_MARKER in result
        assert CLOSING_MARKER in result

    def test_blank_line_separator_present(self):
        result = append_guide("Original description.", SAMPLE_GUIDE)
        assert "\n\n" in result

    def test_append_to_empty_body(self):
        assert append_guide("", SAMPLE_GUIDE) == SAMPLE_GUIDE

    def test_append_to_whitespace_only_body(self):
        assert append_guide("   ", SAMPLE_GUIDE) == SAMPLE_GUIDE

    def test_original_content_comes_before_guide(self):
        result = append_guide("Original.", SAMPLE_GUIDE)
        assert result.index("Original.") < result.index(OPENING_MARKER)


class TestReplaceGuide:
    """Test replacing an existing guide block per SKILL.md Step 5."""

    def _body_with_old_guide(self) -> str:
        old = f"{OPENING_MARKER}\n## Old Guide\n{CLOSING_MARKER}"
        return f"Description.\n\n{old}"

    def test_old_guide_content_removed(self):
        new = f"{OPENING_MARKER}\n## New Guide\n{CLOSING_MARKER}"
        result = replace_guide(self._body_with_old_guide(), new)
        assert "## Old Guide" not in result
        assert "## New Guide" in result

    def test_content_before_marker_preserved(self):
        result = replace_guide(self._body_with_old_guide(), SAMPLE_GUIDE)
        assert "Description." in result

    def test_content_after_marker_preserved(self):
        trailing = f"{OPENING_MARKER}\n## Old Guide\n{CLOSING_MARKER}\n\nTrailing content."
        new = f"{OPENING_MARKER}\n## New Guide\n{CLOSING_MARKER}"
        result = replace_guide(trailing, new)
        assert "Trailing content." in result

    def test_exactly_one_opening_marker(self):
        new = f"{OPENING_MARKER}\n## New Guide\n{CLOSING_MARKER}"
        result = replace_guide(self._body_with_old_guide(), new)
        assert count_occurrences(result, OPENING_MARKER) == 1

    def test_exactly_one_closing_marker(self):
        new = f"{OPENING_MARKER}\n## New Guide\n{CLOSING_MARKER}"
        result = replace_guide(self._body_with_old_guide(), new)
        assert count_occurrences(result, CLOSING_MARKER) == 1


class TestApplyGuide:
    """Test the replace-vs-append dispatch per SKILL.md Step 5."""

    def test_appends_when_no_existing_markers(self):
        body = "Description with no guide."
        result = apply_guide(body, SAMPLE_GUIDE)
        assert "Description with no guide." in result
        assert count_occurrences(result, OPENING_MARKER) == 1

    def test_replaces_when_markers_already_present(self):
        old = f"{OPENING_MARKER}\n## Old Guide\n{CLOSING_MARKER}"
        body = f"Description.\n\n{old}"
        new = f"{OPENING_MARKER}\n## New Guide\n{CLOSING_MARKER}"
        result = apply_guide(body, new)
        assert "## Old Guide" not in result
        assert "## New Guide" in result

    def test_no_duplicate_markers_after_replace(self):
        old = f"{OPENING_MARKER}\n## Old\n{CLOSING_MARKER}"
        body = f"Description.\n\n{old}"
        result = apply_guide(body, SAMPLE_GUIDE)
        assert count_occurrences(result, OPENING_MARKER) == 1
        assert count_occurrences(result, CLOSING_MARKER) == 1
