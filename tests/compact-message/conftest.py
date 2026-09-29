"""Shared helpers for compact-message skill tests.

Reference implementations of the argument rules in SKILL.md's Arguments
section: exact, case-insensitive, whitespace-trimmed help triggers; any
other non-empty text is focus guidance.
"""

from typing import Optional

HELP_TRIGGERS = {"help", "--help", "-h", "?"}


def is_help_request(args: str) -> bool:
    """Check if arguments are a help request per SKILL.md."""
    return args.strip().lower() in HELP_TRIGGERS if args and args.strip() else False


def focus_text(args: str) -> Optional[str]:
    """Return trimmed focus text, or None for empty or help arguments."""
    if not args or not args.strip() or is_help_request(args):
        return None
    return args.strip()
