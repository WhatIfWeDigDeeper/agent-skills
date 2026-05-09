#!/usr/bin/env python3
"""Replace or append a pr-human-guide block in a PR body.

Usage:
    python3 marker-helper.py --body-file FILE --guide-file FILE --out FILE

Reads the current PR body from --body-file, the new guide block from
--guide-file, writes the updated body to --out.

Marker constants use chr(33) for '!' to avoid zsh history expansion when
this script is generated or invoked from an interactive zsh session.
"""

import argparse
import re

OPEN = "<" + chr(33) + "-- pr-human-guide -->"
CLOSE = "<" + chr(33) + "-- /pr-human-guide -->"


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
        after_open = body[start + len(OPEN):].lstrip("\n")
        if after_open.startswith("## Review Guide"):
            anchored.append((start, end))
        complete.append((start, end))

    if anchored:
        return anchored[-1]
    if complete:
        return complete[-1]
    return None


def update_body(body: str, guide: str) -> str:
    """Return body with the guide block replaced or appended."""
    bounds = _find_replacement_bounds(body)
    if bounds is not None:
        start, end = bounds
        before = body[:start]
        after = body[end:]
        # Strip any stray extra markers outside the replaced region so a
        # smuggled fake marker cannot outlast the replacement.
        after = after.replace(OPEN, "").replace(CLOSE, "")
        before = before.replace(OPEN, "").replace(CLOSE, "")
        return before + guide + after
    # No existing block — append with a blank-line separator.
    separator = "\n\n" if body and not body.endswith("\n\n") else ""
    return body + separator + guide


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--body-file", required=True, help="Path to current PR body")
    parser.add_argument("--guide-file", required=True, help="Path to new guide content")
    parser.add_argument("--out", required=True, help="Path to write updated body")
    args = parser.parse_args()

    with open(args.body_file, encoding="utf-8") as f:
        body = f.read()
    with open(args.guide_file, encoding="utf-8") as f:
        guide = f.read()

    result = update_body(body, guide)

    with open(args.out, "w", encoding="utf-8") as f:
        f.write(result)


if __name__ == "__main__":
    main()
