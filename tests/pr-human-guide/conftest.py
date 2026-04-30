"""Pytest fixtures and helpers for pr-human-guide skill tests."""

import hashlib
import re

HELP_TRIGGERS = {"help", "--help", "-h", "?"}

OPENING_MARKER = "<!-- pr-human-guide -->"
CLOSING_MARKER = "<!-- /pr-human-guide -->"

# Regression sentinels for SKILL.md instruction-level guards, not runtime sanitizers.
PROMPT_INJECTION_PATTERNS = (
    re.compile(r"ignore\s+(all\s+)?previous\s+instructions", re.IGNORECASE),
    re.compile(r"do\s+not\s+(add|create|write|update)\s+(a\s+)?(review\s+)?guide", re.IGNORECASE),
    re.compile(r"mark\s+(this\s+)?(pr\s+)?as\s+(safe|no\s+areas)", re.IGNORECASE),
    re.compile(r"use\s+(these\s+)?markers?\s+instead", re.IGNORECASE),
    re.compile(r"print\s+(the\s+)?(token|secret|api\s+key)", re.IGNORECASE),
)


def is_help_request(args: str | None) -> bool:
    """Return True if args is a help trigger per SKILL.md Step 1."""
    return args.strip().lower() in HELP_TRIGGERS if args and args.strip() else False


def parse_pr_argument(args: str | None) -> dict:
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
    cleaned = stripped.removeprefix("#")
    if cleaned.isdigit():
        return {"type": "pr_number", "number": int(cleaned)}
    return {"type": "detect"}


def has_existing_guide(body: str) -> bool:
    """Return True if body already contains a pr-human-guide block per SKILL.md Step 5."""
    return OPENING_MARKER in body


def replace_guide(body: str, new_guide: str) -> str:
    """Replace the existing guide block with new_guide per SKILL.md Step 5.

    new_guide must include the opening and closing markers.
    Prefers a marker immediately followed by the Review Guide heading when
    multiple marker-like blocks are present in untrusted PR body text.
    Preserves all content before the opening marker and after the closing marker
    when present. If the closing marker is missing, replaces from the opening
    marker to the end of body.
    """
    review_guide_marker = re.compile(re.escape(OPENING_MARKER) + r"\r?\n## Review Guide")
    match = review_guide_marker.search(body)
    if match:
        start = match.start()
    else:
        start = body.index(OPENING_MARKER)
    closing_start = body.find(CLOSING_MARKER, start + len(OPENING_MARKER))
    end = (
        closing_start + len(CLOSING_MARKER)
        if closing_start != -1
        else len(body)
    )
    return body[:start] + new_guide + body[end:]


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

    Matches the documented cross-platform workflow: hash the raw file path bytes
    with SHA-256 and use the lowercase hex digest as the GitHub diff anchor.

    Equivalent shell implementations use ``printf '%s'`` so no trailing newline is
    included before selecting ``sha256sum`` or ``shasum -a 256``.
    """
    return hashlib.sha256(file_path.encode()).hexdigest()


def build_diff_link(owner: str, repo: str, pr_number: int, file_path: str) -> str:
    """Build the full GitHub diff anchor link for a file per SKILL.md Step 4."""
    anchor = compute_diff_anchor(file_path)
    return f"https://github.com/{owner}/{repo}/pull/{pr_number}/files#diff-{anchor}"


def escape_markdown_link_label(text: str) -> str:
    """Escape file paths before placing them in markdown link labels."""
    return (
        text.replace("\\", "\\\\")
        .replace("`", "\\`")
        .replace("[", "\\[")
        .replace("]", "\\]")
        .replace("(", "\\(")
        .replace(")", "\\)")
    )


def contains_prompt_injection_instruction(text: str) -> bool:
    """Return True when untrusted PR content looks like agent instructions."""
    return any(pattern.search(text) for pattern in PROMPT_INJECTION_PATTERNS)


def sanitize_guide_reason(reason: str) -> str:
    """Summarize unsafe prompt-like content without copying it as a directive."""
    if contains_prompt_injection_instruction(reason) or OPENING_MARKER in reason or CLOSING_MARKER in reason:
        return "Changed content contains prompt-like text; review the surrounding code as data."
    return reason


def diff_mentions_auth_keywords(diff_text: str) -> bool:
    """Detect known auth/security keywords as a regression sentinel."""
    security_terms = ("jwt.verify", "requireRole", "authorization", "permission", "secret")
    return any(term in diff_text for term in security_terms)
