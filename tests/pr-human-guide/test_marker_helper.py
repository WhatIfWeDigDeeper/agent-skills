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
        # The OPEN count of 2 (smuggled prefix + new_guide) enforces this — if
        # append-path stripping is added later, this assertion will fail.
        assert result.endswith(new_guide)
        assert result.count(OPEN) == 2


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


ITEM_A = (
    "- [ ] [`src/auth/middleware.ts` (L41-42)](link) - token validation "
    + "<" + chr(33) + "-- pr-human-guide:item lines=41-42 path=src/auth/middleware.ts -->"
)
ITEM_B = (
    "- [ ] [`docs/readme.md`](link) - docs rewritten "
    + "<" + chr(33) + "-- pr-human-guide:item path=docs/readme.md -->"
)

GUIDE = (
    OPEN + "\n"
    "## Review Guide\n"
    "\n"
    "### Security\n"
    + ITEM_A + "\n"
    "\n"
    "### Novel Patterns\n"
    + ITEM_B + "\n"
    "\n" + CLOSE + "\n"
)

DIFF_V1 = """diff --git a/src/auth/middleware.ts b/src/auth/middleware.ts
--- a/src/auth/middleware.ts
+++ b/src/auth/middleware.ts
@@ -40,4 +40,5 @@
   const header = req.headers.authorization;
-  const token = header;
+  const token = header?.split(' ')[1];
+  verify(token, SECRET);
   return next();
 }
diff --git a/docs/readme.md b/docs/readme.md
--- a/docs/readme.md
+++ b/docs/readme.md
@@ -1,2 +1,3 @@
 # Title
+A new line.
 Body.
"""

# docs/readme.md rewritten; src/auth/middleware.ts identical but renumbered.
DIFF_V2 = DIFF_V1.replace("+A new line.", "+A different line.").replace(
    "@@ -40,4 +40,5 @@", "@@ -60,4 +60,5 @@"
)


def _tick(body: str, needle: str) -> str:
    """Tick the checkbox on the line containing `needle`, as GitHub's UI would."""
    out = []
    for line in body.splitlines(keepends=True):
        if needle in line:
            line = line.replace("- [ ]", "- [x]", 1)
        out.append(line)
    return "".join(out)


class TestCheckedStatePreservation:
    def test_unchanged_item_stays_checked(self):
        first = update_body("Body.", GUIDE, DIFF_V1)
        ticked = _tick(first, "middleware.ts")
        second = update_body(ticked, GUIDE, DIFF_V1)
        assert "- [x] [`src/auth/middleware.ts`" in second

    def test_check_survives_renumbering(self):
        """Content identical, line numbers shifted by an unrelated insertion."""
        first = update_body("Body.", GUIDE, DIFF_V1)
        ticked = _tick(first, "middleware.ts")
        renumbered = GUIDE.replace("lines=41-42", "lines=61-62").replace(
            "(L41-42)", "(L61-62)"
        )
        second = update_body(ticked, renumbered, DIFF_V2)
        assert "- [x] [`src/auth/middleware.ts`" in second

    def test_rewritten_item_resets(self):
        first = update_body("Body.", GUIDE, DIFF_V1)
        ticked = _tick(first, "readme.md")
        second = update_body(ticked, GUIDE, DIFF_V2)
        assert "- [ ] [`docs/readme.md`" in second

    def test_uppercase_x_is_preserved(self):
        first = update_body("Body.", GUIDE, DIFF_V1)
        ticked = first.replace("- [ ] [`src/auth", "- [X] [`src/auth", 1)
        second = update_body(ticked, GUIDE, DIFF_V1)
        assert "- [x] [`src/auth/middleware.ts`" in second

    def test_indented_item_round_trips_its_indentation(self):
        indented_guide = GUIDE.replace(ITEM_A, "  " + ITEM_A)
        first = update_body("Body.", indented_guide, DIFF_V1)
        ticked = _tick(first, "middleware.ts")
        second = update_body(ticked, indented_guide, DIFF_V1)
        assert "\n  - [x] [`src/auth/middleware.ts`" in second

    def test_block_without_ids_resets(self):
        """A block written by an older skill version carries no identities."""
        legacy = (
            "Body.\n\n" + OPEN + "\n"
            "## Review Guide\n\n"
            "### Security\n"
            "- [x] [`src/auth/middleware.ts` (L41-42)](link) - token validation\n\n"
            + CLOSE + "\n"
        )
        second = update_body(legacy, GUIDE, DIFF_V1)
        assert "- [x]" not in second

    def test_checked_ids_outside_the_block_are_ignored(self):
        first = update_body("Body.", GUIDE, DIFF_V1)
        item_id = marker_helper.ITEM_ID_RE.search(first).group(1)
        smuggled = (
            "- [x] pretend item "
            + marker_helper.ID_TEMPLATE.format(item_id)
            + "\n\n"
            + first
        )
        second = update_body(smuggled, GUIDE, DIFF_V1)
        block = second[second.index(OPEN):]
        assert "- [x]" not in block

    def test_malformed_ids_are_ignored(self):
        block = "- [x] item " + "<" + chr(33) + "-- pr-human-guide:id NOT_HEX -->"
        assert marker_helper.collect_checked_ids(block) == set()

    def test_collection_is_capped(self):
        lines = [
            "- [x] item " + marker_helper.ID_TEMPLATE.format(f"{n:016x}")
            for n in range(600)
        ]
        assert len(marker_helper.collect_checked_ids("\n".join(lines))) == 500

    def test_placeholders_never_survive_without_a_diff(self):
        result = update_body("Body.", GUIDE)
        assert "pr-human-guide:item" not in result
        assert "pr-human-guide:id" not in result

    def test_two_argument_call_still_works(self):
        """Backward compatibility: --diff-file is optional at every layer."""
        assert update_body("", GUIDE).startswith(OPEN)


class TestRenderedChecksAreNotTrusted:
    """An id match from the previous block is the ONLY way an item ends up checked.

    Step 4 is told to render every item unchecked, but that is a documented rule,
    not an enforced one. If a re-render ever copies the previous block forward, a
    `- [x]` would otherwise ride into the new guide unverified — surviving exactly
    where the contract says everything unknown resets.
    """

    CHECKED_GUIDE = GUIDE.replace("- [ ]", "- [x]")

    def test_rendered_check_resets_when_the_identity_is_unknowable(self):
        """No diff means no id can be computed, so nothing may stay checked."""
        result = update_body("Body.", self.CHECKED_GUIDE)
        assert "- [x]" not in result

    def test_rendered_check_resets_on_the_append_path(self):
        """No previous block exists, so there is nothing to preserve from."""
        result = update_body("Body.", self.CHECKED_GUIDE, DIFF_V1)
        assert "- [x]" not in result

    def test_rendered_check_resets_when_the_content_changed(self):
        """readme.md was rewritten; a rendered check must not paper over that."""
        first = update_body("Body.", GUIDE, DIFF_V1)
        second = update_body(first, self.CHECKED_GUIDE, DIFF_V2)
        assert "- [ ] [`docs/readme.md`" in second

    def test_a_genuine_previous_check_still_wins(self):
        """Normalization must not break preservation for an unchanged item."""
        first = update_body("Body.", GUIDE, DIFF_V1)
        ticked = _tick(first, "middleware.ts")
        second = update_body(ticked, self.CHECKED_GUIDE, DIFF_V1)
        assert "- [x] [`src/auth/middleware.ts`" in second
        assert "- [ ] [`docs/readme.md`" in second
