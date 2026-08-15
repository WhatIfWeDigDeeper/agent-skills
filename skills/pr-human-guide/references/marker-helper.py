#!/usr/bin/env python3
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


def _find_replacement_bounds(body: str) -> tuple[int, int] | None:
    """Return (start, end) of the guide block to replace, or None to append.

    Prefers the last complete block whose opening marker is immediately followed
    by '## Review Guide'. Falls back to the last complete block. Treats extra
    or incomplete markers as untrusted text that cannot shift bounds.
    """
    open_positions = [m.start() for m in re.finditer(re.escape(OPEN), body)]
    anchored: list[tuple[int, int]] = []
    complete: list[tuple[int, int]] = []

    for idx, start in enumerate(open_positions):
        # Only search for CLOSE before the next OPEN
        next_open = open_positions[idx + 1] if idx + 1 < len(open_positions) else len(body)
        close_pos = body.find(CLOSE, start + len(OPEN))
        if close_pos == -1 or close_pos >= next_open:
            continue
        end = close_pos + len(CLOSE)
        after_open = body[start + len(OPEN):]
        # Lockstep with skills/pr-human-guide/references/output-format.md: the
        # opening marker must be immediately followed by a newline and
        # '## Review Guide' (no blank line between them). If that template
        # changes, update this regex to match —
        # otherwise every real block silently falls through to the `complete`
        # fallback below.
        if re.match(r"\r?\n## Review Guide", after_open):
            anchored.append((start, end))
        complete.append((start, end))

    if anchored:
        return anchored[-1]
    if complete:
        return complete[-1]
    return None


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


CHECKED_ITEM_RE = re.compile(
    r"^\s*[-*+]\s+\[[xX]\].*?"
    + "<" + chr(33) + r"-- pr-human-guide:id ([0-9a-f]{16}) -->"
)
UNCHECKED_BOX_RE = re.compile(r"^(\s*[-*+]\s+\[)\s(\])")
# Exactly the `### Category` line output-format.md emits -- not `##` (the block's
# own "## Review Guide") and not a deeper `####`. Matching any heading level would
# fold a non-category subheading into the identity, resetting a reviewer's check
# on an item whose category never changed.
CATEGORY_HEADING_RE = re.compile(r"^###\s+\S")


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
        if CATEGORY_HEADING_RE.match(stripped):
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


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--body-file", required=True, help="Path to current PR body")
    parser.add_argument("--guide-file", required=True, help="Path to new guide content")
    parser.add_argument("--out", required=True, help="Path to write updated body")
    parser.add_argument(
        "--diff-file",
        help="Path to the unified diff; enables checked-state preservation",
    )
    args = parser.parse_args()

    with open(args.body_file, encoding="utf-8") as f:
        body = f.read()
    with open(args.guide_file, encoding="utf-8") as f:
        guide = f.read()

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

    with open(args.out, "w", encoding="utf-8") as f:
        f.write(result)


if __name__ == "__main__":
    main()
