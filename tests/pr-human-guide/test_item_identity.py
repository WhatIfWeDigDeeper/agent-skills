"""Diff-anchored item identity in the shipped marker-helper.py.

Imports the real helper rather than reimplementing it, so the hash these tests
pin is the hash the skill actually posts into a PR body.
"""

import importlib.util
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
HELPER_PATH = REPO_ROOT / "skills" / "pr-human-guide" / "references" / "marker-helper.py"

_spec = importlib.util.spec_from_file_location("marker_helper_identity", HELPER_PATH)
marker_helper = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(marker_helper)

# Hunk header math: 3 context + 1 deletion = old count 4; 3 context + 2
# additions = new count 5. New-side numbering runs 40, 41, 42, 43, 44.
DIFF = """diff --git a/src/auth/middleware.ts b/src/auth/middleware.ts
index 1111111..2222222 100644
--- a/src/auth/middleware.ts
+++ b/src/auth/middleware.ts
@@ -40,4 +40,5 @@ export function auth() {
   const header = req.headers.authorization;
-  const token = header;
+  const token = header?.split(' ')[1];
+  verify(token, SECRET);
   return next();
 }
diff --git a/docs/readme.md b/docs/readme.md
index 3333333..4444444 100644
--- a/docs/readme.md
+++ b/docs/readme.md
@@ -1,2 +1,3 @@
 # Title
+A new line.
 Body.
"""

# Same content, shifted 10 lines down by an unrelated insertion above it.
DIFF_SHIFTED = DIFF.replace("@@ -40,4 +40,5 @@", "@@ -50,4 +50,5 @@")

# Same range, one line inside it rewritten.
DIFF_EDITED = DIFF.replace("verify(token, SECRET);", "verifyStrict(token, SECRET);")

HEADING = "### Security"
PATH = "src/auth/middleware.ts"
RANGE = (41, 42)

PLACEHOLDER = (
    "<" + chr(33) + "-- pr-human-guide:item lines=41-42 path=src/auth/middleware.ts -->"
)

GUIDE_WITH_PLACEHOLDERS = (
    marker_helper.OPEN + "\n"
    "## Review Guide\n"
    "\n"
    "### Security\n"
    "- [ ] [`src/auth/middleware.ts` (L41-42)](link) - token validation "
    + PLACEHOLDER + "\n"
    "\n" + marker_helper.CLOSE + "\n"
)


class TestSelectDiffLines:
    def test_selects_only_in_range_lines(self):
        selected = marker_helper._select_diff_lines(DIFF, PATH, RANGE)
        assert selected == [
            "-  const token = header;",
            "+  const token = header?.split(' ')[1];",
            "+  verify(token, SECRET);",
        ]

    def test_ignores_hunks_for_other_paths(self):
        selected = marker_helper._select_diff_lines(DIFF, "docs/readme.md", None)
        assert selected == [" # Title", "+A new line.", " Body."]

    def test_whole_file_takes_every_body_line(self):
        selected = marker_helper._select_diff_lines(DIFF, PATH, None)
        assert len(selected) == 6
        assert selected[0] == "   const header = req.headers.authorization;"
        assert selected[-1] == " }"

    def test_unknown_path_selects_nothing(self):
        assert marker_helper._select_diff_lines(DIFF, "nope/missing.ts", None) == []

    def test_body_line_starting_with_plus_plus_plus_is_content(self):
        """A hunk body line may look like a '+++ ' file header; counts decide."""
        diff = (
            "diff --git a/notes.txt b/notes.txt\n"
            "--- a/notes.txt\n"
            "+++ b/notes.txt\n"
            "@@ -1,1 +1,2 @@\n"
            " keep\n"
            "+++ plus prefixed\n"
        )
        assert marker_helper._select_diff_lines(diff, "notes.txt", None) == [
            " keep",
            "+++ plus prefixed",
        ]


class TestComputeItemId:
    def test_returns_sixteen_lowercase_hex(self):
        item_id = marker_helper.compute_item_id(HEADING, PATH, DIFF, RANGE)
        assert item_id is not None
        assert len(item_id) == 16
        assert all(c in "0123456789abcdef" for c in item_id)

    def test_identical_content_at_shifted_line_numbers_is_stable(self):
        """The headline property: renumbering must not reset a reviewer's check."""
        original = marker_helper.compute_item_id(HEADING, PATH, DIFF, RANGE)
        shifted = marker_helper.compute_item_id(HEADING, PATH, DIFF_SHIFTED, (51, 52))
        assert original == shifted

    def test_edited_line_inside_range_changes_the_id(self):
        original = marker_helper.compute_item_id(HEADING, PATH, DIFF, RANGE)
        edited = marker_helper.compute_item_id(HEADING, PATH, DIFF_EDITED, RANGE)
        assert not (original == edited)

    def test_different_heading_changes_the_id(self):
        security = marker_helper.compute_item_id(HEADING, PATH, DIFF, RANGE)
        novel = marker_helper.compute_item_id("### Novel Patterns", PATH, DIFF, RANGE)
        assert not (security == novel)

    def test_whole_file_id_differs_from_ranged_id(self):
        whole = marker_helper.compute_item_id(HEADING, PATH, DIFF, None)
        ranged = marker_helper.compute_item_id(HEADING, PATH, DIFF, RANGE)
        assert not (whole == ranged)

    def test_unknown_path_yields_no_id(self):
        assert marker_helper.compute_item_id(HEADING, "nope/missing.ts", DIFF, None) is None

    def test_missing_diff_yields_no_id(self):
        assert marker_helper.compute_item_id(HEADING, PATH, None, RANGE) is None
        assert marker_helper.compute_item_id(HEADING, PATH, "", RANGE) is None

    def test_missing_path_yields_no_id(self):
        assert marker_helper.compute_item_id(HEADING, None, DIFF, RANGE) is None


class TestParseLineRange:
    def test_parses_a_range(self):
        assert marker_helper._parse_line_range("42-67") == (42, 67)

    def test_parses_a_single_line(self):
        assert marker_helper._parse_line_range("42") == (42, 42)

    def test_rejects_garbage(self):
        assert marker_helper._parse_line_range("L42-67") is None
        assert marker_helper._parse_line_range("67-42") is None
        assert marker_helper._parse_line_range("") is None
        assert marker_helper._parse_line_range(None) is None


class TestResolveItemPlaceholders:
    def test_placeholder_becomes_an_id_comment(self):
        resolved = marker_helper.resolve_item_placeholders(GUIDE_WITH_PLACEHOLDERS, DIFF)
        expected = marker_helper.compute_item_id(HEADING, PATH, DIFF, RANGE)
        assert marker_helper.ID_TEMPLATE.format(expected) in resolved
        assert "pr-human-guide:item" not in resolved

    def test_placeholder_is_stripped_without_a_diff(self):
        resolved = marker_helper.resolve_item_placeholders(GUIDE_WITH_PLACEHOLDERS, None)
        assert "pr-human-guide:item" not in resolved
        assert "pr-human-guide:id" not in resolved
        assert resolved.rstrip().endswith(marker_helper.CLOSE)

    def test_unknown_path_strips_the_placeholder_and_its_leading_space(self):
        guide = GUIDE_WITH_PLACEHOLDERS.replace(
            "path=src/auth/middleware.ts", "path=nope/missing.ts"
        )
        resolved = marker_helper.resolve_item_placeholders(guide, DIFF)
        assert "pr-human-guide:item" not in resolved
        assert "- token validation\n" in resolved

    def test_identity_forged_in_the_guide_is_discarded(self):
        """Identities must be computed here, never carried in from rendered text."""
        forged = GUIDE_WITH_PLACEHOLDERS.replace(
            PLACEHOLDER, marker_helper.ID_TEMPLATE.format("0123456789abcdef")
        )
        resolved = marker_helper.resolve_item_placeholders(forged, DIFF)
        assert "0123456789abcdef" not in resolved

    def test_heading_is_taken_from_the_enclosing_category(self):
        under_novel = GUIDE_WITH_PLACEHOLDERS.replace("### Security", "### Novel Patterns")
        security_id = marker_helper.ITEM_ID_RE.search(
            marker_helper.resolve_item_placeholders(GUIDE_WITH_PLACEHOLDERS, DIFF)
        ).group(1)
        novel_id = marker_helper.ITEM_ID_RE.search(
            marker_helper.resolve_item_placeholders(under_novel, DIFF)
        ).group(1)
        assert not (security_id == novel_id)


class TestRenderingContract:
    """The model's half of the two-phase identity, pinned in output-format.md.

    Both rules are load-bearing and no unit test can catch a violation: a drifted
    line range or a re-posted previous block still parses, it just silently loses
    a reviewer's checkmark (or, worse, keeps a stale one).
    """

    OUTPUT_FORMAT_MD = (
        REPO_ROOT / "skills" / "pr-human-guide" / "references" / "output-format.md"
    )

    def test_range_is_pinned_to_the_changed_lines(self):
        text = self.OUTPUT_FORMAT_MD.read_text()
        assert "must span **exactly the\nchanged lines**" in text
        assert "never the whole `@@`\nhunk" in text

    def test_rerun_must_rerender_rather_than_repost(self):
        text = self.OUTPUT_FORMAT_MD.read_text()
        assert "**Render the block fresh on every run, re-runs included.**" in text
        assert "Never copy the previous" in text
