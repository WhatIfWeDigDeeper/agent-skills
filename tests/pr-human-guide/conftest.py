"""Pytest fixtures and helpers for pr-human-guide skill tests."""

import hashlib
import re

HELP_TRIGGERS = {"help", "--help", "-h", "?"}

OPENING_MARKER = "<!-- pr-human-guide -->"
CLOSING_MARKER = "<!-- /pr-human-guide -->"


def is_help_request(args: str) -> bool:
    """Return True if args is a help trigger per SKILL.md Step 1."""
    return args.strip().lower() in HELP_TRIGGERS if args and args.strip() else False


def parse_pr_argument(args: str) -> dict:
    """Parse the optional PR number argument per SKILL.md Step 1.

    Returns:
        {"type": "help"}                         if a help trigger
        {"type": "pr_number", "number": int}     if numeric (with optional # prefix)
        {"type": "detect"}                       if empty/whitespace (auto-detect from branch)
    """
    if not args or not args.strip():
        return {"type": "detect"}
    stripped = args.strip()
    if is_help_request(stripped):
        return {"type": "help"}
    cleaned = stripped.lstrip("#")
    if cleaned.isdigit():
        return {"type": "pr_number", "number": int(cleaned)}
    return {"type": "detect"}


def has_existing_guide(body: str) -> bool:
    """Return True if body already contains a pr-human-guide block per SKILL.md Step 5."""
    return OPENING_MARKER in body


def replace_guide(body: str, new_guide: str) -> str:
    """Replace the existing guide block with new_guide per SKILL.md Step 5.

    new_guide must include the opening and closing markers.
    Preserves all content before the opening marker and after the closing marker.
    """
    start = body.index(OPENING_MARKER)
    end = body.index(CLOSING_MARKER) + len(CLOSING_MARKER)
    before = body[:start].rstrip("\n")
    after = body[end:].lstrip("\n")
    parts = [p for p in [before, new_guide, after] if p]
    return "\n\n".join(parts)


def append_guide(body: str, new_guide: str) -> str:
    """Append new_guide to body with a blank-line separator per SKILL.md Step 5."""
    if not body or not body.strip():
        return new_guide
    return body.rstrip("\n") + "\n\n" + new_guide


def apply_guide(body: str, new_guide: str) -> str:
    """Apply new_guide: replace if markers already exist, else append."""
    if has_existing_guide(body):
        return replace_guide(body, new_guide)
    return append_guide(body, new_guide)


def count_occurrences(text: str, substring: str) -> int:
    """Count non-overlapping occurrences of substring in text."""
    return text.count(substring)


def format_terminal_report(
    pr_number: int,
    pr_title: str,
    pr_url: str,
    item_count: int,
    category_count: int,
    was_updated: bool,
) -> str:
    """Format the terminal report per SKILL.md Step 6.

    Uses 'updated on' when replacing an existing guide, 'added to' for a new one.
    When item_count is 0, the count line is omitted — the guide body already
    contains the 'no areas' message.
    """
    action = "updated on" if was_updated else "added to"
    lines = [f"Review guide {action} PR #{pr_number}: {pr_title}"]
    if item_count > 0:
        lines.append(f"{item_count} item(s) across {category_count} category/categories.")
    lines.append(pr_url)
    return "\n".join(lines)


def compute_diff_anchor(file_path: str) -> str:
    """Compute the SHA-256 diff anchor for a file path per SKILL.md Step 4.

    Mirrors the shell command:
        printf '%s' "path" | (sha256sum 2>/dev/null || shasum -a 256) | cut -d' ' -f1

    printf '%s' does not append a newline, so the hash covers the raw path bytes only.
    """
    return hashlib.sha256(file_path.encode()).hexdigest()


def build_diff_link(owner: str, repo: str, pr_number: int, file_path: str) -> str:
    """Build the full GitHub diff anchor link for a file per SKILL.md Step 4."""
    anchor = compute_diff_anchor(file_path)
    return f"https://github.com/{owner}/{repo}/pull/{pr_number}/files#diff-{anchor}"
