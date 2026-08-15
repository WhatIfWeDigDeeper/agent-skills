# pr-human-guide: Preserve Checked Guide Items — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Carry a reviewer's `- [x]` across a `/pr-human-guide` re-run for exactly those items whose anchored diff content is byte-identical, and reset every other item.

**Architecture:** Step 4 (the model) renders each item with a trailing placeholder comment restating `path` and `lines`. Step 5's `marker-helper.py` parses the unified diff, replaces each placeholder with `<!-- pr-human-guide:id HASH -->` where the hash covers the enclosing category heading, the path, and the anchored diff lines (line *numbers* excluded), then re-checks any item whose id was checked in the previous canonical block. The model never computes a hash; everything hashable lives in Python and is unit-tested against the shipped helper.

**Tech Stack:** Python 3 stdlib (`argparse`, `hashlib`, `re`); markdown skill definitions; bash snippets that must stay `set -u`-safe and zsh-history-expansion-safe; pytest via `uv run --with pytest`; `snyk-agent-scan` baselines under `evals/security/`.

**Spec:** [`specs/56-pr-human-guide-preserve-checked-items/plan.md`](plan.md)

## Global Constraints

- **Version bump:** `skills/pr-human-guide/SKILL.md` frontmatter `version: "0.15"` → `"0.16"`. Exactly **one** bump for the whole PR, made in Task 1. Do not bump again in Tasks 2–6.
- **Never write a literal `!` inside a `<!--` sequence in Python source or in a shell string.** `marker-helper.py` builds every marker from `chr(33)`; new patterns must do the same. In bash, single-quote any pattern containing `!`. Interactive zsh performs history expansion and silently rewrites `<!--` to `<\!--`.
- **Do not add a second `trap`.** `commands.md` sets one EXIT trap; a shell keeps only the most recent one, so a second silently replaces the first and leaks temp files.
- **Do not hardcode `/tmp/`.** Use `mktemp`, `$TMPDIR`, or `/private/tmp` as the `${TMPDIR:-…}` fallback.
- **Backward compatibility:** `update_body(body, guide)` must keep working with two positional arguments — existing tests call it that way, and `--diff-file` is optional at the CLI.
- **Everything unknown resets to `- [ ]`.** No code path may leave an item checked when its identity could not be recomputed from this run's diff.
- **`collect_checked_ids` is only ever called on the previous canonical block**, never on the whole PR body.
- **Leave the `## Review Guide` anchor line alone** — `marker-helper.py`'s `re.match(r"\r?\n## Review Guide", …)`, its lockstep comment, `output-format.md`'s lockstep note, and `tests/pr-human-guide/conftest.py::_select_guide_bounds` all depend on it.
- **Do not reimplement preservation in `tests/pr-human-guide/conftest.py`.** It already carries a drifted parallel copy of the block-selection logic; preservation tests import the shipped helper directly.
- Run tests with sandbox restrictions lifted (in Claude Code: `dangerouslyDisableSandbox: true`) — `uv run --with pytest` hits a cache EPERM otherwise, and `git push` does too because `pre-push` runs pytest.
- Restrict every commit with an explicit pathspec (`git commit -m … -- <paths>`) and follow the repo's commit-message conventions, trailers included.
- Check off each `- [ ]` in this file as you complete it — immediately, not batched at the end.

---

### Task 1: Diff-anchored item identity

**Files:**
- Create: `tests/pr-human-guide/test_item_identity.py`
- Modify: `skills/pr-human-guide/references/marker-helper.py` (imports, new constants, new functions)
- Modify: `skills/pr-human-guide/SKILL.md` (frontmatter `version` only)

**Interfaces:**
- Consumes: nothing from earlier tasks.
- Produces:
  - `compute_item_id(heading: str, path: str | None, diff_text: str | None, line_range: tuple[int, int] | None = None) -> str | None` — 16 lowercase hex chars, or `None` when it cannot be computed.
  - `_select_diff_lines(diff_text: str, path: str, line_range: tuple[int, int] | None) -> list[str]`
  - `_parse_line_range(raw: str | None) -> tuple[int, int] | None`
  - Module constants `ITEM_PLACEHOLDER_RE`, `ITEM_ID_RE`, `ID_TEMPLATE`, `HUNK_HEADER_RE`.
  - Task 2 consumes all of these.

- [x] **Step 1: Confirm no version bump already exists on this branch**

```bash
git fetch origin && git diff origin/main -- skills/pr-human-guide/SKILL.md | rg '^\+  version:'
```

Expected: no output. If it prints a line, the bump already landed — skip Step 8.

- [x] **Step 2: Write the failing identity tests**

Create `tests/pr-human-guide/test_item_identity.py`:

```python
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
        assert original != edited

    def test_different_heading_changes_the_id(self):
        security = marker_helper.compute_item_id(HEADING, PATH, DIFF, RANGE)
        novel = marker_helper.compute_item_id("### Novel Patterns", PATH, DIFF, RANGE)
        assert security != novel

    def test_whole_file_id_differs_from_ranged_id(self):
        assert marker_helper.compute_item_id(
            HEADING, PATH, DIFF, None
        ) != marker_helper.compute_item_id(HEADING, PATH, DIFF, RANGE)

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
```

- [x] **Step 3: Run the tests to verify they fail**

```bash
uv run --with pytest pytest tests/pr-human-guide/test_item_identity.py -v
```

Expected: FAIL — `AttributeError: module 'marker_helper_identity' has no attribute '_select_diff_lines'`.

- [x] **Step 4: Add the imports and constants to `marker-helper.py`**

Replace the `import argparse` / `import re` block and the two marker constants with:

```python
import argparse
import hashlib
import re
import sys

OPEN = "<" + chr(33) + "-- pr-human-guide -->"
CLOSE = "<" + chr(33) + "-- /pr-human-guide -->"

# Lockstep with skills/pr-human-guide/references/output-format.md: Step 4 renders
# each item with a trailing ':item' placeholder comment, and this helper rewrites
# it to an ':id' identity comment. If that template changes, update these patterns
# — otherwise every item loses its identity and every reviewer's checked box
# resets on every re-run, silently.
ITEM_PLACEHOLDER_RE = re.compile("<" + chr(33) + r"-- pr-human-guide:item\s+([^>]*?)-->")
ITEM_ID_RE = re.compile("<" + chr(33) + r"-- pr-human-guide:id ([0-9a-f]{16}) -->")
ID_TEMPLATE = "<" + chr(33) + "-- pr-human-guide:id {} -->"
HUNK_HEADER_RE = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")
```

- [x] **Step 5: Add the diff-selection helpers**

Insert immediately after `_find_replacement_bounds` and before `update_body`:

```python
def _strip_diff_path(raw: str) -> str | None:
    """Return the repo-relative path from the value of a '+++ ' diff header."""
    raw = raw.split("\t", 1)[0].strip()
    if not raw or raw == "/dev/null":
        return None
    if raw.startswith("b/"):
        raw = raw[2:]
    return raw


def _parse_line_range(raw: str | None) -> tuple[int, int] | None:
    """Parse a 'lines=42-67' (or 'lines=42') value; None if absent or malformed."""
    if not raw:
        return None
    text = raw.strip()
    match = re.fullmatch(r"(\d+)-(\d+)", text)
    if match:
        start, end = int(match.group(1)), int(match.group(2))
        return (start, end) if start <= end else None
    match = re.fullmatch(r"(\d+)", text)
    if match:
        value = int(match.group(1))
        return (value, value)
    return None


def _in_range(cursor: int, line_range: tuple[int, int] | None) -> bool:
    if line_range is None:
        return True
    return line_range[0] <= cursor <= line_range[1]


def _select_diff_lines(
    diff_text: str, path: str, line_range: tuple[int, int] | None
) -> list[str]:
    """Return `path`'s diff body lines whose new-side position falls in range.

    Hunk bodies are consumed by decrementing the old/new line counts declared in
    the '@@' header rather than by guessing where a hunk ends, so a body line that
    happens to begin '+++ ' or '--- ' parses as content, not as a file header.
    Deletions are kept when the cursor is in range even though they do not advance
    it — a pure deletion inside a flagged range must change the item's identity.
    """
    selected: list[str] = []
    current: str | None = None
    old_left = new_left = 0
    cursor = 0

    for line in diff_text.splitlines():
        if old_left > 0 or new_left > 0:
            if line.startswith("\\"):  # '\ No newline at end of file'
                continue
            if line.startswith("-"):
                old_left -= 1
                if current == path and _in_range(cursor, line_range):
                    selected.append(line)
                continue
            if line.startswith("+"):
                new_left -= 1
                if current == path and _in_range(cursor, line_range):
                    selected.append(line)
                cursor += 1
                continue
            if line.startswith(" ") or line == "":
                old_left -= 1
                new_left -= 1
                if current == path and _in_range(cursor, line_range):
                    selected.append(line)
                cursor += 1
                continue
            # Malformed body — abandon the hunk and re-read this line as a header.
            old_left = new_left = 0

        match = HUNK_HEADER_RE.match(line)
        if match:
            old_left = int(match.group(2)) if match.group(2) is not None else 1
            new_left = int(match.group(4)) if match.group(4) is not None else 1
            cursor = int(match.group(3))
            continue
        if line.startswith("+++ "):
            current = _strip_diff_path(line[4:])

    return selected


def compute_item_id(
    heading: str,
    path: str | None,
    diff_text: str | None,
    line_range: tuple[int, int] | None = None,
) -> str | None:
    """Return a stable 16-hex identity for a guide item, or None if unknowable.

    Keyed on the enclosing category heading, the file path, and the anchored diff
    lines — deliberately NOT on the line numbers, so an unrelated insertion above
    the range does not reset a reviewer's check.
    """
    if not path or not diff_text:
        return None
    selected = _select_diff_lines(diff_text, path, line_range)
    if not selected:
        return None
    payload = "\n".join([heading or "", path, *selected])
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]
```

- [x] **Step 6: Run the tests to verify they pass**

```bash
uv run --with pytest pytest tests/pr-human-guide/test_item_identity.py -v
```

Expected: PASS (all classes). If `test_selects_only_in_range_lines` fails, print
`marker_helper._select_diff_lines(DIFF, PATH, None)` and check the cursor
arithmetic against the hunk-header comment in the test file.

- [x] **Step 7: Update the module docstring**

Replace the `Usage:` line and add a sentence, so the docstring matches the CLI Task 2 ships:

```python
"""Replace or append a pr-human-guide block in a PR body.

Usage:
    python3 marker-helper.py --body-file FILE --guide-file FILE --out FILE \\
        [--diff-file FILE]

Reads the current PR body from --body-file, the new guide block from
--guide-file, writes the updated body to --out.

--diff-file is optional and enables checked-state preservation: item placeholders
in the guide are resolved to content hashes computed from the diff, and an item
checked in the previous block stays checked when its hash is unchanged. Without
it, placeholders are stripped and every item renders unchecked.

Marker constants use chr(33) for '!' so the OPEN/CLOSE strings are not
present as literal tokens in the source — zsh history expansion would
otherwise corrupt them during edits or copies in an interactive shell.
"""
```

- [x] **Step 8: Bump the skill version**

In `skills/pr-human-guide/SKILL.md` frontmatter: `version: "0.15"` → `version: "0.16"`.
This is the **only** bump in the PR.

- [x] **Step 9: Commit**

```bash
git add tests/pr-human-guide/test_item_identity.py skills/pr-human-guide/references/marker-helper.py skills/pr-human-guide/SKILL.md
git commit -m "feat(pr-human-guide): compute diff-anchored identities for guide items" -- tests/pr-human-guide/test_item_identity.py skills/pr-human-guide/references/marker-helper.py skills/pr-human-guide/SKILL.md
```

---

### Task 2: Placeholder resolution and checked-state preservation

**Files:**
- Modify: `skills/pr-human-guide/references/marker-helper.py` (`resolve_item_placeholders`, `collect_checked_ids`, `apply_checked`, `update_body`, `main`)
- Modify: `tests/pr-human-guide/test_item_identity.py` (placeholder-resolution class)
- Modify: `tests/pr-human-guide/test_marker_helper.py` (preservation class)
- Modify: `tests/pr-human-guide/conftest.py` (one comment)

**Interfaces:**
- Consumes: `compute_item_id`, `_parse_line_range`, `ITEM_PLACEHOLDER_RE`, `ITEM_ID_RE`, `ID_TEMPLATE` from Task 1.
- Produces:
  - `resolve_item_placeholders(guide: str, diff_text: str | None = None) -> str`
  - `collect_checked_ids(block: str, limit: int = 500) -> set[str]`
  - `apply_checked(guide: str, checked: set[str]) -> str`
  - `update_body(body: str, guide: str, diff_text: str | None = None) -> str`
  - CLI flag `--diff-file` (optional). Task 3 wires `commands.md` to pass it.

- [x] **Step 1: Write the failing placeholder-resolution tests**

Append to `tests/pr-human-guide/test_item_identity.py`:

```python
GUIDE_WITH_PLACEHOLDERS = (
    marker_helper.OPEN + "\n"
    "## Review Guide\n"
    "\n"
    "### Security\n"
    "- [ ] [`src/auth/middleware.ts` (L41-42)](link) - token validation "
    + "<" + chr(33) + "-- pr-human-guide:item lines=41-42 path=src/auth/middleware.ts -->\n"
    "\n" + marker_helper.CLOSE + "\n"
)


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
            "<" + chr(33) + "-- pr-human-guide:item lines=41-42 path=src/auth/middleware.ts -->",
            marker_helper.ID_TEMPLATE.format("0123456789abcdef"),
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
        assert security_id != novel_id
```

- [x] **Step 2: Run them to verify they fail**

```bash
uv run --with pytest pytest tests/pr-human-guide/test_item_identity.py::TestResolveItemPlaceholders -v
```

Expected: FAIL — `AttributeError: … has no attribute 'resolve_item_placeholders'`.

- [x] **Step 3: Implement resolution and preservation**

Insert after `compute_item_id` in `marker-helper.py`:

```python
CHECKED_ITEM_RE = re.compile(
    r"^\s*[-*+]\s+\[[xX]\].*?"
    + "<" + chr(33) + r"-- pr-human-guide:id ([0-9a-f]{16}) -->"
)
UNCHECKED_BOX_RE = re.compile(r"^(\s*[-*+]\s+\[)\s(\])")


def _parse_item_attrs(raw: str) -> dict[str, str]:
    """Parse 'lines=42-67 path=src/foo.ts' into a dict; unknown keys are ignored."""
    attrs: dict[str, str] = {}
    for token in raw.split():
        key, sep, value = token.partition("=")
        if sep:
            attrs[key] = value
    return attrs


def resolve_item_placeholders(guide: str, diff_text: str | None = None) -> str:
    """Rewrite Step 4 item placeholders into identity comments.

    Any identity comment already present in the rendered guide is discarded first,
    so every identity in the output was computed here from `diff_text`. A
    placeholder that cannot be resolved is removed entirely and its item renders
    unchecked.
    """
    guide = ITEM_ID_RE.sub("", guide)
    resolved: list[str] = []
    heading = ""

    for line in guide.splitlines(keepends=True):
        stripped = line.lstrip()
        if stripped.startswith("#"):
            heading = stripped.strip()
        match = ITEM_PLACEHOLDER_RE.search(line)
        if match:
            attrs = _parse_item_attrs(match.group(1))
            item_id = compute_item_id(
                heading,
                attrs.get("path"),
                diff_text,
                _parse_line_range(attrs.get("lines")),
            )
            head, tail = line[: match.start()], line[match.end() :]
            line = head + ID_TEMPLATE.format(item_id) + tail if item_id else head.rstrip() + tail
        resolved.append(line)

    # Identity is per item, so any further placeholder on a line is surplus.
    return ITEM_PLACEHOLDER_RE.sub("", "".join(resolved))


def collect_checked_ids(block: str, limit: int = 500) -> set[str]:
    """Return identity hashes found on checked item lines.

    `block` MUST be the previous canonical guide block only — never the whole PR
    body. Callers slice it with the bounds from `_find_replacement_bounds`, so a
    checked line smuggled into surrounding body text cannot reach the new guide.
    """
    found: set[str] = set()
    for line in block.splitlines():
        if len(found) >= limit:
            break
        match = CHECKED_ITEM_RE.match(line)
        if match:
            found.add(match.group(1))
    return found


def apply_checked(guide: str, checked: set[str]) -> str:
    """Re-check items whose identity was checked in the previous block."""
    if not checked:
        return guide
    out: list[str] = []
    for line in guide.splitlines(keepends=True):
        match = ITEM_ID_RE.search(line)
        if match and match.group(1) in checked:
            line = UNCHECKED_BOX_RE.sub(r"\1x\2", line, count=1)
        out.append(line)
    return "".join(out)
```

Then replace `update_body` with:

```python
def update_body(body: str, guide: str, diff_text: str | None = None) -> str:
    """Return body with the guide block replaced or appended.

    Placeholders are resolved on both paths — the append path included, or a
    first run would post raw placeholders into the PR body.
    """
    bounds = _find_replacement_bounds(body)
    guide = resolve_item_placeholders(guide, diff_text)
    if bounds is not None:
        start, end = bounds
        guide = apply_checked(guide, collect_checked_ids(body[start:end]))
        before = body[:start]
        after = body[end:]
        # Strip any stray extra markers outside the replaced region so a
        # smuggled fake marker cannot outlast the replacement.
        after = after.replace(OPEN, "").replace(CLOSE, "")
        before = before.replace(OPEN, "").replace(CLOSE, "")
        return before + guide + after
    # No existing block — append with a single blank-line separator.
    if not body or not body.strip():
        return guide
    return body.rstrip("\n") + "\n\n" + guide
```

- [x] **Step 4: Add the `--diff-file` CLI flag**

In `main()`, after the `--out` argument:

```python
    parser.add_argument(
        "--diff-file",
        help="Path to the unified diff; enables checked-state preservation",
    )
```

and replace the `result = update_body(body, guide)` line with:

```python
    diff_text = None
    if args.diff_file:
        try:
            with open(args.diff_file, encoding="utf-8") as f:
                diff_text = f.read()
        except OSError as exc:
            print(
                f"warning: cannot read --diff-file {args.diff_file} ({exc}); "
                "checked state will reset",
                file=sys.stderr,
            )
            diff_text = None
        else:
            if not diff_text.strip():
                print(
                    f"warning: --diff-file {args.diff_file} is empty; "
                    "checked state will reset",
                    file=sys.stderr,
                )
                diff_text = None

    result = update_body(body, guide, diff_text)
```

- [x] **Step 5: Run the resolution tests to verify they pass**

```bash
uv run --with pytest pytest tests/pr-human-guide/test_item_identity.py -v
```

Expected: PASS.

- [x] **Step 6: Write the failing preservation tests**

Append to `tests/pr-human-guide/test_marker_helper.py`. It already imports the
shipped helper as `marker_helper`; reuse that.

```python
ITEM_A = (
    "- [ ] [`src/auth/middleware.ts` (L41-42)](link) - token validation "
    + "<" + chr(33) + "-- pr-human-guide:item lines=41-42 path=src/auth/middleware.ts -->"
)
ITEM_B = (
    "- [ ] [`docs/readme.md`](link) - docs rewritten "
    + "<" + chr(33) + "-- pr-human-guide:item path=docs/readme.md -->"
)

GUIDE = (
    marker_helper.OPEN + "\n"
    "## Review Guide\n"
    "\n"
    "### Security\n"
    + ITEM_A + "\n"
    "\n"
    "### Novel Patterns\n"
    + ITEM_B + "\n"
    "\n" + marker_helper.CLOSE + "\n"
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
        first = marker_helper.update_body("Body.", GUIDE, DIFF_V1)
        ticked = _tick(first, "middleware.ts")
        second = marker_helper.update_body(ticked, GUIDE, DIFF_V1)
        assert "- [x] [`src/auth/middleware.ts`" in second

    def test_check_survives_renumbering(self):
        """Content identical, line numbers shifted by an unrelated insertion."""
        first = marker_helper.update_body("Body.", GUIDE, DIFF_V1)
        ticked = _tick(first, "middleware.ts")
        renumbered = GUIDE.replace("lines=41-42", "lines=61-62").replace("(L41-42)", "(L61-62)")
        second = marker_helper.update_body(ticked, renumbered, DIFF_V2)
        assert "- [x] [`src/auth/middleware.ts`" in second

    def test_rewritten_item_resets(self):
        first = marker_helper.update_body("Body.", GUIDE, DIFF_V1)
        ticked = _tick(first, "readme.md")
        second = marker_helper.update_body(ticked, GUIDE, DIFF_V2)
        assert "- [ ] [`docs/readme.md`" in second

    def test_uppercase_x_is_preserved(self):
        first = marker_helper.update_body("Body.", GUIDE, DIFF_V1)
        ticked = first.replace("- [ ] [`src/auth", "- [X] [`src/auth", 1)
        second = marker_helper.update_body(ticked, GUIDE, DIFF_V1)
        assert "- [x] [`src/auth/middleware.ts`" in second

    def test_indented_item_round_trips_its_indentation(self):
        indented_guide = GUIDE.replace(ITEM_A, "  " + ITEM_A)
        first = marker_helper.update_body("Body.", indented_guide, DIFF_V1)
        ticked = _tick(first, "middleware.ts")
        second = marker_helper.update_body(ticked, indented_guide, DIFF_V1)
        assert "\n  - [x] [`src/auth/middleware.ts`" in second

    def test_block_without_ids_resets(self):
        """A block written by an older skill version carries no identities."""
        legacy = (
            "Body.\n\n" + marker_helper.OPEN + "\n"
            "## Review Guide\n\n"
            "### Security\n"
            "- [x] [`src/auth/middleware.ts` (L41-42)](link) - token validation\n\n"
            + marker_helper.CLOSE + "\n"
        )
        second = marker_helper.update_body(legacy, GUIDE, DIFF_V1)
        assert "- [x]" not in second

    def test_checked_ids_outside_the_block_are_ignored(self):
        first = marker_helper.update_body("Body.", GUIDE, DIFF_V1)
        item_id = marker_helper.ITEM_ID_RE.search(first).group(1)
        smuggled = (
            "- [x] pretend item " + marker_helper.ID_TEMPLATE.format(item_id) + "\n\n" + first
        )
        second = marker_helper.update_body(smuggled, GUIDE, DIFF_V1)
        block = second[second.index(marker_helper.OPEN) :]
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
        result = marker_helper.update_body("Body.", GUIDE)
        assert "pr-human-guide:item" not in result
        assert "pr-human-guide:id" not in result

    def test_two_argument_call_still_works(self):
        """Backward compatibility: --diff-file is optional at every layer."""
        assert marker_helper.update_body("", GUIDE).startswith(marker_helper.OPEN)
```

- [x] **Step 7: Run them to verify they pass**

```bash
uv run --with pytest pytest tests/pr-human-guide/ -v
```

Expected: PASS, including the pre-existing `TestAppend` / `TestReplace` /
`TestStrayMarkerStripping` / `TestCRLFAnchoring` / `TestIncompleteMarkers` classes.

- [x] **Step 8: Record the design decision in `conftest.py`**

Add above `_select_guide_bounds`:

```python
# Checked-state preservation is deliberately NOT mirrored here. This module's
# copy of the block-selection logic has already drifted from the shipped helper
# (see the docstring in test_marker_helper.py); preservation is tested against
# skills/pr-human-guide/references/marker-helper.py directly instead.
```

- [x] **Step 9: Commit**

```bash
git add skills/pr-human-guide/references/marker-helper.py tests/pr-human-guide/
git commit -m "feat(pr-human-guide): preserve checked items whose anchored content is unchanged" -- skills/pr-human-guide/references/marker-helper.py tests/pr-human-guide/
```

---

### Task 3: Wire the skill's reference files

**Files:**
- Modify: `skills/pr-human-guide/references/output-format.md`
- Modify: `skills/pr-human-guide/references/commands.md`
- Modify: `tests/pr-human-guide/test_helper_path_resolution.py`

**Interfaces:**
- Consumes: the `--diff-file` flag and the placeholder grammar from Tasks 1–2.
- Produces: the rendered placeholder contract Step 4 follows, and the `DIFF_FILE` shell contract Step 5 follows.

- [x] **Step 1: Write the failing text assertions**

Append to `tests/pr-human-guide/test_helper_path_resolution.py` (inside the class
that already reads `COMMANDS_MD`, matching its existing style):

```python
    def test_helper_is_passed_the_diff_file(self):
        """Preservation is inert unless Step 5 hands the helper the diff."""
        text = COMMANDS_MD.read_text()
        assert '--diff-file "$DIFF_FILE"' in text
        assert 'DIFF_FILE="${TMPDIR:-/private/tmp}/pr-human-guide-diff-${pr_number}.diff"' in text

    def test_single_exit_trap_covers_the_diff_file(self):
        """A second trap would silently replace the first and leak temp files."""
        text = COMMANDS_MD.read_text()
        assert text.count("trap '") == 1
        assert 'trap \'rm -f "$BODY_FILE" "$OUT_FILE" "$GUIDE_FILE" "$DIFF_FILE"\'' in text
```

- [x] **Step 2: Run them to verify they fail**

```bash
uv run --with pytest pytest tests/pr-human-guide/test_helper_path_resolution.py -v
```

Expected: FAIL on both new tests with `AssertionError`.

- [x] **Step 3: Save the diff in Step 2 of `commands.md`**

Replace the fenced block under "## Gather the diff (Step 2)" and the sentence
after it:

````markdown
```bash
# Step 5 re-derives this same path to give marker-helper.py the diff, which is
# what lets a reviewer's checked items survive the re-run. Keep the two spellings
# identical.
DIFF_FILE="${TMPDIR:-/private/tmp}/pr-human-guide-diff-${pr_number}.diff"
gh pr diff "${pr_number}" --name-only
gh pr diff "${pr_number}" > "$DIFF_FILE" || {
  echo "Could not fetch the diff for PR #${pr_number} with 'gh pr diff'." >&2
  exit 1
}
cat "$DIFF_FILE"
```

Store the full diff for analysis. Store the file list separately. The saved
`$DIFF_FILE` is consumed again by Step 5 and removed by its cleanup trap.
````

- [x] **Step 4: Pass `--diff-file` in Step 5 of `commands.md`**

Three edits inside the Step 5 bash block:

Add after the `GUIDE_FILE=` assignment:

```bash
# Written by Step 2; re-derived here because shell variables do not survive
# between tool calls. marker-helper tolerates it being missing or empty — it
# warns and every item renders unchecked, which is the pre-0.16 behavior.
DIFF_FILE="${TMPDIR:-/private/tmp}/pr-human-guide-diff-${pr_number}.diff"
```

Extend the existing trap (do **not** add a second one):

```bash
# One EXIT trap per shell — a second `trap ... EXIT` replaces this one and leaks
# the files it covered. Add new temp paths here rather than in another trap.
trap 'rm -f "$BODY_FILE" "$OUT_FILE" "$GUIDE_FILE" "$DIFF_FILE"' EXIT INT TERM
```

Extend the helper invocation:

```bash
# --diff-file is what enables checked-state preservation. If it is missing or
# empty the helper warns on stderr and every item renders unchecked — pass it
# unconditionally rather than building the argument list conditionally.
python3 "$HELPER" \
  --body-file "$BODY_FILE" \
  --guide-file "$GUIDE_FILE" \
  --diff-file "$DIFF_FILE" \
  --out "$OUT_FILE"
```

Also update the trailing comment `# Trap fires on shell exit and removes
BODY_FILE/OUT_FILE/GUIDE_FILE.` to include `DIFF_FILE`.

- [x] **Step 5: Add the placeholder to the entry template in `output-format.md`**

Replace the "Format each entry as:" block and the line under it:

````markdown
Format each entry as:

```
- [ ] [`path/to/file` (L{start}-{end})](link) — one-line reason <!-- pr-human-guide:item lines={start}-{end} path=path/to/file -->
```

Omit the line range if changes are spread across the whole file — from the label
**and** from the placeholder (`<!-- pr-human-guide:item path=path/to/file -->`).

`{start}` and `{end}` are new-side line numbers and must span **exactly the
changed lines** the entry covers — the `+` lines, plus any `-` lines falling
between them — never the surrounding context lines and never the whole `@@`
hunk. Step 5 hashes the diff lines this range selects, so a range that includes
a context line on one run but not the next yields two different identities and
silently drops a reviewer's checkmark. When an entry covers several changed
regions in one file, use the first changed line as `{start}` and the last as
`{end}`.

### Per-item identity comment

The trailing `pr-human-guide:item` comment is a placeholder. Emit it on every
item; restate the same `path` and line range you used in the label, unquoted and
without whitespace inside a value. Do **not** compute a hash and do **not** write
a `pr-human-guide:id` comment — Step 5's `marker-helper.py` replaces each
placeholder with `<!-- pr-human-guide:id HASH -->`, where the hash is derived from
the anchored diff content, and uses it to restore any box a reviewer had checked
whose content is unchanged. A placeholder it cannot resolve is removed and that
item renders unchecked, so a wrong `path=` costs a reviewer's checkmark but
corrupts nothing.

**Render the block fresh on every run, re-runs included.** Build each entry from
the current diff and emit the `:item` placeholder again. Never copy the previous
block out of the PR body, and never write a `:id` comment yourself — a re-posted
block carries its old `- [x]` marks through verbatim, including on items whose
code has since been rewritten, and drops the placeholders the next run needs.
Preservation is Step 5's job; reproducing it by hand defeats it.

This is unrelated to the `#diff-{ANCHOR}` fragment above: that anchor hashes the
file *path* (GitHub's own scheme) and never changes when the file's content does.
````

Both added paragraphs came out of a deterministic dry run of the eval-15 fixture
against the shipped helper before the eval was spawned: only a perfectly-shifted,
same-width range preserved the check (`41-42` → `61-62` did, `41-42` → `60-64`
did not), and re-posting the resolved block kept a stale `- [x]` on an item whose
content had been rewritten. Both are model-side failures no unit test reaches, so
`tests/pr-human-guide/test_item_identity.py::TestRenderingContract` pins the prose.

- [x] **Step 6: Add placeholders to the with-items example in `output-format.md`**

In the ```markdown example block, extend the three item lines:

```markdown
### Security
- [ ] [`src/auth/middleware.ts` (L42-67)](link) — New token validation logic <!-- pr-human-guide:item lines=42-67 path=src/auth/middleware.ts -->

### Config / Infrastructure
- [ ] [`deploy/terraform/iam.tf` (L12-18)](link) — IAM role permissions widened <!-- pr-human-guide:item lines=12-18 path=deploy/terraform/iam.tf -->

### Novel Patterns
- [ ] [`src/cache/redis.ts`](link) — First use of Redis in this codebase; no existing caching pattern to reference <!-- pr-human-guide:item path=src/cache/redis.ts -->
```

Leave the `## Review Guide` line, the marker lines, and the "no flagged items"
block exactly as they are.

- [x] **Step 7: Run the tests to verify they pass**

```bash
uv run --with pytest pytest tests/pr-human-guide/ -v
```

Expected: PASS.

- [x] **Step 8: Commit**

```bash
git add skills/pr-human-guide/references/ tests/pr-human-guide/test_helper_path_resolution.py
git commit -m "feat(pr-human-guide): render item placeholders and feed the diff to the helper" -- skills/pr-human-guide/references/ tests/pr-human-guide/test_helper_path_resolution.py
```

---

### Task 4: SKILL.md prose

**Files:**
- Modify: `skills/pr-human-guide/SKILL.md` (Security model, Step 4, Step 5, Notes)

**Interfaces:**
- Consumes: everything from Tasks 1–3.
- Produces: no code interface. This is the documented contract reviewers read.

- [x] **Step 1: Add the Security-model bullet**

Insert after the "Body written via file, not argv" bullet, before the "Residual
risks:" paragraph:

```markdown
- **Checked-state preservation is content-keyed and body-independent** — on re-run
  the helper reads the previous canonical block only, extracts identity hashes
  matching `^[0-9a-f]{16}$` from `- [x]` lines (capped at 500), and carries across a
  single boolean per hash; no text from the untrusted body reaches the new guide.
  Hashes are recomputed by the helper from the `gh pr diff` output, never read from
  the body, so a forged identity cannot make a check survive a content change.
  Preservation grants no capability a body editor lacks — anyone able to edit the
  PR body can already type `- [x]` (Step 5).
```

- [x] **Step 2: Note the saved diff in Step 2**

Append to the Step 2 paragraph, after "capture the full diff and the changed-file
list separately":

```markdown
. The section also saves the diff to a temp file that Step 5 hands to
`marker-helper.py` for checked-state preservation.
```

- [x] **Step 3: Note the placeholder in Step 4**

Append a sentence to the paragraph that begins "**You must now execute
[`references/output-format.md`](references/output-format.md)**":

```markdown
Emit the per-item `<!-- pr-human-guide:item … -->` placeholder that
`output-format.md` specifies on every entry — restate the path and line range,
never a hash; Step 5 resolves it.
```

- [x] **Step 4: Note preservation in Step 5**

Append to the Step 5 paragraph, after "guards against empty/corrupted output, and
posts via `gh pr edit --body-file`":

```markdown
The helper also resolves each item placeholder to a content hash and restores any
box a reviewer had checked whose anchored content is unchanged.
```

- [x] **Step 5: Rewrite the Notes bullet**

Replace the single Notes bullet with:

```markdown
- **Idempotency**: Re-runs replace the whole `<!-- pr-human-guide -->` block, and
  content outside it is preserved verbatim. A `- [x]` a reviewer checked is carried
  across only when that item's anchored diff content is byte-identical to the
  previous run — line numbers may shift, the content may not. Everything else
  resets to `- [ ]`: an item whose code changed, an item whose identity could not
  be recomputed, and every item in a block written before v0.16.
```

- [x] **Step 6: Verify no second version bump crept in**

```bash
git diff origin/main -- skills/pr-human-guide/SKILL.md | rg '^\+  version:'
```

Expected: exactly one line, `+  version: "0.16"`.

- [x] **Step 7: Spell-check and commit**

```bash
npx cspell skills/pr-human-guide/SKILL.md skills/pr-human-guide/references/output-format.md skills/pr-human-guide/references/commands.md specs/56-pr-human-guide-preserve-checked-items/plan.md specs/56-pr-human-guide-preserve-checked-items/tasks.md
git add skills/pr-human-guide/SKILL.md
git commit -m "docs(pr-human-guide): document content-keyed checked-state preservation" -- skills/pr-human-guide/SKILL.md
```

Add any flagged term to `cspell.config.yaml` in its correct alphabetical position
and include that file in the commit.

---

### Task 5: Eval 15 and benchmark

**Files:**
- Modify: `evals/pr-human-guide/evals.json`
- Modify: `evals/pr-human-guide/benchmark.json`
- Modify: `evals/pr-human-guide/benchmark.md`
- Modify: `README.md`

**Interfaces:**
- Consumes: the shipped behavior from Tasks 1–4.
- Produces: recorded runs for eval 15 in both configurations.

- [x] **Step 1: Add eval 15 to `evals.json`**

Two-turn by design: turn 1 writes the guide, turn 2 asks for a refresh after the
reviewer has ticked a box. This avoids pinning a hash value into the fixture — the
executor's own turn-1 output supplies the identities.

```json
{
  "id": 15,
  "name": "preserves-checked-unchanged-items",
  "prompt": "Can you add a review guide to the description of PR #77 so reviewers know where to look?\n\nPR #77 — 'Harden auth and widen the deploy role'\nURL: https://github.com/owner/repo/pull/77\n\nThe current PR description is:\n```\nHardens token handling and updates the deploy role policy.\n```\n\nThe diff:\n\n```diff\ndiff --git a/src/auth/middleware.ts b/src/auth/middleware.ts\nindex 1111111..2222222 100644\n--- a/src/auth/middleware.ts\n+++ b/src/auth/middleware.ts\n@@ -40,4 +40,5 @@ export function auth(req, res, next) {\n   const header = req.headers.authorization;\n-  const token = header;\n+  const token = header?.split(' ')[1];\n+  verify(token, SECRET);\n   return next();\n }\ndiff --git a/deploy/terraform/iam.tf b/deploy/terraform/iam.tf\nindex 3333333..4444444 100644\n--- a/deploy/terraform/iam.tf\n+++ b/deploy/terraform/iam.tf\n@@ -12,4 +12,4 @@ resource \"aws_iam_role_policy\" \"app\" {\n   policy = jsonencode({\n-    Action = [\"s3:GetObject\"]\n+    Action = [\"s3:GetObject\", \"s3:PutObject\"]\n   })\n }\n```",
  "followup_prompt": "Thanks — I went through both entries and ticked both checkboxes in the description.\n\nNew commits just landed. Here's the current diff — please refresh the review guide.\n\n```diff\ndiff --git a/src/auth/middleware.ts b/src/auth/middleware.ts\nindex 1111111..5555555 100644\n--- a/src/auth/middleware.ts\n+++ b/src/auth/middleware.ts\n@@ -1,0 +1,19 @@\n+/*\n+ * Copyright (c) 2026 Example Corp.\n+ * Licensed under the MIT License.\n+ */\n+\n+\n+\n+\n+\n+\n+\n+\n+\n+\n+\n+\n+\n+\n+\n@@ -40,4 +60,5 @@ export function auth(req, res, next) {\n   const header = req.headers.authorization;\n-  const token = header;\n+  const token = header?.split(' ')[1];\n+  verify(token, SECRET);\n   return next();\n }\ndiff --git a/deploy/terraform/iam.tf b/deploy/terraform/iam.tf\nindex 3333333..6666666 100644\n--- a/deploy/terraform/iam.tf\n+++ b/deploy/terraform/iam.tf\n@@ -12,4 +12,4 @@ resource \"aws_iam_role_policy\" \"app\" {\n   policy = jsonencode({\n-    Action = [\"s3:GetObject\"]\n+    Action = [\"s3:GetObject\", \"s3:PutObject\", \"s3:DeleteObject\"]\n   })\n }\n```",
  "expected_output": "On the second turn the agent should replace the existing guide block rather than append a second one. The reviewer had ticked both entries. The src/auth/middleware.ts entry must stay checked — its anchored content is byte-identical and only its line numbers moved, pushed down by a new license header. The deploy/terraform/iam.tf entry must reset to unchecked — its path, hunk header, and changed line number are all unchanged, but the line's content was rewritten to widen the action list again. Neither fact is stated in the prompt; the agent has to derive both by comparing the two diffs. An agent that copies the previous block through keeps both ticks and fails the reset case; one that re-renders from scratch resets both and fails the preserve case. The posted description must contain no unresolved pr-human-guide:item placeholder text.",
  "assertions": [
    {
      "id": "unchanged-item-stays-checked",
      "text": "In the refreshed PR description, the src/auth/middleware.ts entry is still checked ('- [x]') even though its line numbers shifted"
    },
    {
      "id": "rewritten-item-resets",
      "text": "In the refreshed PR description, the deploy/terraform/iam.tf entry is unchecked ('- [ ]') even though the reviewer had ticked it, because its content was rewritten"
    },
    {
      "id": "no-placeholder-leaks",
      "text": "The refreshed PR description contains no literal 'pr-human-guide:item' placeholder text"
    }
  ]
}
```

Insert it as the last element of the `evals` array; the preceding element's `}`
needs a trailing comma. Then validate:

```bash
python3 -c 'import json; d=json.load(open("evals/pr-human-guide/evals.json")); print(len(d["evals"]), d["evals"][-1]["id"])'
```

Expected: `15 15`.

- [x] **Step 2: Run the `with_skill` configuration**

Spawn an executor subagent with `mode: "auto"`. Prompt it to `mktemp -d` a
workspace under `${TMPDIR:-/private/tmp}`, `cd` in, and work only there. Give it
the eval `prompt` as the first user message and the `followup_prompt` as a second
message after turn 1 completes; require `SUMMARY_TURN1` / `SUMMARY_TURN2` and the
final PR body verbatim. Tell it to read `skills/pr-human-guide/SKILL.md` and its
`references/` and follow them directly — and **not** to call the `Skill` tool.
Pass **no** assertion text.

- [x] **Step 3: Run the `without_skill` configuration**

Same prompts and workspace rules, minus the skill: forbid reading anything under
`skills/pr-human-guide/`, and again forbid the `Skill` tool. Pass **no** assertion
text.

- [x] **Step 4: Grade both transcripts**

Spawn a grader subagent per configuration with the **full assertion text strings**
from Step 1 pasted into the prompt. Require `grading.json` shaped
`{"summary": {"passed", "failed", "total", "pass_rate"}, "expectations": [{"text", "passed", "evidence"}]}`
with repo-relative evidence paths and quoted transcript excerpts.

- [x] **Step 5: Check per-branch discrimination**

Read both gradings before recording anything. Requirement: eval 15 must have at
least one assertion failing `without_skill`.

Expect `unchanged-item-stays-checked` to be the weak discriminator — a baseline
that copies the previous block through verbatim passes it by accident while
failing `rewritten-item-resets`. That is acceptable; record it in the run notes.
If **both** branch assertions pass `without_skill`, the prompt is too easy for
copy-through: strengthen it (e.g. require the reason text to reflect the new
`docs/setup.md` content) and re-run — do **not** re-grade.

**This fired, and the first fixture turned out to have three separate flaws** —
found by running it, not by reading it. The baseline scored 3/3, but not by
copy-through:

1. **The prompt narrated the answer.** Turn 2 said the license header "pushed the
   auth change further down the file but did not alter it" and that
   `docs/setup.md` "was rewritten". An agent told which item is unchanged does
   not need content-keyed identity to tick the right box. Removed.
2. **The reset item was outside the six categories.** `docs/setup.md` is
   documentation prose, so a correct `with_skill` run never flags it — the reset
   assertion had no entry to bind to. Replaced with `deploy/terraform/iam.tf`,
   which Config / Infrastructure flags squarely (it is the category's own example
   in `output-format.md`).
3. **The reset assertion was vacuous.** The reviewer ticked only the auth entry,
   so "the other entry is unchecked" was trivially true for every agent — that,
   not copy-through, is what the baseline was passing. The reviewer now ticks
   **both** entries.

The rebuilt fixture holds `deploy/terraform/iam.tf` at the same path, the same
hunk header, and the same changed line (13) across both turns, differing only in
the line's content — the case path-, range-, and text-keyed matching all get
wrong. An agent that copies the previous block through keeps both ticks and fails
the reset assertion; one that re-renders from scratch resets both and fails the
preserve assertion. Only content-keyed identity passes both. Verified against the
shipped helper before re-running: the auth id is stable across turns while the
iam.tf id changes. The two earlier run pairs were discarded, not recorded.

- [x] **Step 6: Record the runs in `benchmark.json`**

Append two run entries (`eval_id: 15`, `eval_name: "preserves-checked-unchanged-items"`,
`run_number: 1`, one per configuration) with `expectations` from the gradings and
per-run stats extracted via
[`evals/scripts/extract_subagent_usage.py`](../../evals/scripts/extract_subagent_usage.py).
Use `null` — never `0` — for anything not measured.

Also: append `15` to `metadata.evals_run`; add a `models_tested` entry for the
executor/analyzer model actually used, noting it is a partial set covering eval 15
only; set `metadata.skill_version` to `"0.16"`; recompute `run_summary` and the
matching `run_summary_by_model` bucket with **sample** stddev (N−1) and signed
2-decimal delta strings computed from unrounded means.

Validate:

```bash
python3 -c 'import json; json.load(open("evals/pr-human-guide/benchmark.json"))'
jq '[.runs[] | .expectations[] | select((. | keys) != ["evidence","passed","text"])] | length' evals/pr-human-guide/benchmark.json
```

Expected: no output from the first, `0` from the second.

- [x] **Step 7: Update `benchmark.md`**

Four edits: a Summary-table row for eval 15; a `### Eval 15 — \`preserves-checked-unchanged-items\``
section; the "N of M" token-denominator sentence (find the sentence beginning
"Token statistics are computed only over"); and a `### v0.16` subsection under
"Known Eval Limitations" recording the two-turn design, the model the runs used,
and the weak-discriminator note from Step 5.

- [x] **Step 8: Update `README.md`**

Update the `pr-human-guide` row's `Eval Δ` column and the **Eval cost** bullet in
its Skill Notes section to match the recomputed `run_summary`.

- [x] **Step 9: Commit**

```bash
git add evals/pr-human-guide/ README.md
git commit -m "test(pr-human-guide): add eval 15 for checked-state preservation" -- evals/pr-human-guide/ README.md
```

---

### Task 6: Security baseline, full verification, and PR

**Files:**
- Modify: `evals/security/pr-human-guide.baseline.json`
- Modify: `cspell.config.yaml` (only if a new term is flagged)
- Modify: `specs/56-pr-human-guide-preserve-checked-items/tasks.md` (checkboxes)

**Interfaces:**
- Consumes: everything from Tasks 1–5.
- Produces: a pushed branch and a PR.

- [x] **Step 1: Refresh the security baseline**

```bash
bash evals/security/scan.sh --update-baselines --confirm
```

Then set `skill_version` to `"0.16"` in
`evals/security/pr-human-guide.baseline.json` if the script did not, and append
one sentence to the running `notes` log describing this change. Confirm no
finding beyond the pinned `W011` appeared:

```bash
git diff evals/security/pr-human-guide.baseline.json
```

- [x] **Step 2: Run the full test suite**

```bash
uv run --with pytest pytest tests/ -v
```

Expected: PASS. Sandbox restrictions must be lifted.

- [x] **Step 3: Spell-check every changed markdown file**

```bash
git diff --name-only origin/main | rg '\.md$' | xargs npx cspell
```

Add flagged terms to `cspell.config.yaml` in alphabetical position. Do not pipe
cspell output through `grep -v` — an npm cache EPERM would be swallowed.

- [x] **Step 4: Confirm every task checkbox in this file is ticked**

```bash
rg -n '^- \[ \] \*\*Step' specs/56-pr-human-guide-preserve-checked-items/tasks.md
```

Expected: no output.

- [x] **Step 5: Commit and push**

```bash
git add evals/security/pr-human-guide.baseline.json cspell.config.yaml specs/56-pr-human-guide-preserve-checked-items/
git commit -m "chore(pr-human-guide): refresh security baseline for v0.16" -- evals/security/pr-human-guide.baseline.json cspell.config.yaml specs/56-pr-human-guide-preserve-checked-items/
git push -u origin HEAD
```

- [x] **Step 6: Open the PR**

Body must state that it closes #221, summarize the content-keyed rule, and note
the eval-15 result. Then, per repo convention, run `/pr-comments {pr_number}`
immediately after the push — without asking.

- [ ] **Step 7: Dogfood on this PR**

Run `/pr-human-guide` on the new PR, tick a box in the GitHub UI, push a commit
that edits one flagged range, re-run, and confirm the ticked item survived while
the edited one reset. This is the only check that exercises the model end to end;
record the outcome in the PR thread. `/pr-human-guide` is required before
reporting the PR ready for human review in any case.
