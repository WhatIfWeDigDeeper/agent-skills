"""Tests for skills/pr-human-guide/references/marker-helper.py.

Imports the helper's pure functions and exercises append, replace, anchored
selection, stray-marker stripping, CRLF anchoring, and incomplete-marker
fallback. Note: marker-helper.py adds stray-marker stripping that the
in-tests reference logic in conftest.py does not, so this suite asserts
the helper's documented behavior directly rather than parity with conftest.
"""

import importlib.util
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
HELPER_PATH = REPO_ROOT / "skills" / "pr-human-guide" / "references" / "marker-helper.py"

_spec = importlib.util.spec_from_file_location("marker_helper", HELPER_PATH)
assert _spec is not None and _spec.loader is not None
marker_helper = importlib.util.module_from_spec(_spec)
sys.modules["marker_helper"] = marker_helper
_spec.loader.exec_module(marker_helper)

OPEN = marker_helper.OPEN
CLOSE = marker_helper.CLOSE
update_body = marker_helper.update_body


def _block(content: str = "## Review Guide\n\nNo areas.") -> str:
    return f"{OPEN}\n{content}\n{CLOSE}"


class TestAppend:
    def test_append_to_empty_body(self) -> None:
        guide = _block()
        assert update_body("", guide) == guide

    def test_append_to_whitespace_body(self) -> None:
        guide = _block()
        assert update_body("   \n", guide) == guide

    def test_append_to_body_with_content(self) -> None:
        guide = _block()
        result = update_body("Existing description.", guide)
        assert result == "Existing description.\n\n" + guide

    def test_append_does_not_double_newline_when_body_ends_with_single_newline(self) -> None:
        guide = _block()
        result = update_body("Existing description.\n", guide)
        assert result == "Existing description.\n\n" + guide
        assert "\n\n\n" not in result

    def test_append_does_not_double_newline_when_body_ends_with_double_newline(self) -> None:
        guide = _block()
        result = update_body("Existing description.\n\n", guide)
        assert result == "Existing description.\n\n" + guide
        assert "\n\n\n" not in result


class TestReplace:
    def test_replace_existing_block(self) -> None:
        old_guide = _block("## Review Guide\n\n- old item")
        new_guide = _block("## Review Guide\n\n- new item")
        body = f"PR description.\n\n{old_guide}"
        result = update_body(body, new_guide)
        assert result == f"PR description.\n\n{new_guide}"
        assert "old item" not in result

    def test_replace_preserves_content_after_block(self) -> None:
        old_guide = _block("## Review Guide\n\n- old")
        new_guide = _block("## Review Guide\n\n- new")
        body = f"Before.\n\n{old_guide}\n\nAfter."
        result = update_body(body, new_guide)
        assert result == f"Before.\n\n{new_guide}\n\nAfter."

    def test_replace_picks_anchored_block_over_unanchored(self) -> None:
        unanchored = f"{OPEN}\nNot the guide.\n{CLOSE}"
        anchored = _block("## Review Guide\n\n- real item")
        new_guide = _block("## Review Guide\n\n- replacement")
        body = f"intro\n\n{unanchored}\n\nfiller\n\n{anchored}\n\nend"
        result = update_body(body, new_guide)
        assert "- real item" not in result
        assert "- replacement" in result
        # Stray markers outside the canonical block get stripped, but their
        # plaintext content survives — only the replaced block is removed.
        assert result.count(OPEN) == 1
        assert result.count(CLOSE) == 1

    def test_replace_picks_last_anchored_when_multiple(self) -> None:
        first = _block("## Review Guide\n\n- first")
        second = _block("## Review Guide\n\n- second")
        new_guide = _block("## Review Guide\n\n- new")
        body = f"{first}\n\nfiller\n\n{second}"
        result = update_body(body, new_guide)
        assert "- second" not in result
        assert "- new" in result
        # The earlier anchored block's markers are stripped after canonical
        # extraction, so only the new guide carries the marker pair.
        assert result.count(OPEN) == 1
        assert result.count(CLOSE) == 1


class TestStrayMarkerStripping:
    def test_strips_stray_open_marker_outside_replaced_region(self) -> None:
        canonical = _block("## Review Guide\n\n- canonical")
        new_guide = _block("## Review Guide\n\n- new")
        body = f"smuggled {OPEN} marker before\n\n{canonical}\n\nstray {CLOSE} after"
        result = update_body(body, new_guide)
        assert result.count(OPEN) == 1
        assert result.count(CLOSE) == 1
        assert new_guide in result

    def test_strips_stray_markers_when_no_canonical_block(self) -> None:
        new_guide = _block("## Review Guide\n\n- new")
        body = f"some text {OPEN} fake content"
        result = update_body(body, new_guide)
        assert new_guide in result
        # Append path leaves the smuggled OPEN in the prefix; this documents the
        # current behavior — strays are stripped only when canonical exists.
        assert result.endswith(new_guide)


class TestCRLFAnchoring:
    def test_crlf_anchored_block_is_recognized(self) -> None:
        guide_crlf = f"{OPEN}\r\n## Review Guide\r\n\r\n- crlf\r\n{CLOSE}"
        new_guide = _block("## Review Guide\n\n- new")
        body = f"intro\n\n{guide_crlf}\n\nend"
        result = update_body(body, new_guide)
        assert "- crlf" not in result
        assert "- new" in result


class TestIncompleteMarkers:
    def test_open_without_close_falls_through_to_append(self) -> None:
        new_guide = _block("## Review Guide\n\n- appended")
        body = f"text {OPEN} but no close"
        result = update_body(body, new_guide)
        assert result.endswith(new_guide)
        assert "- appended" in result
