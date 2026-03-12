"""Pytest fixtures for ship-it skill tests."""

import re

HELP_TRIGGERS = {"help", "--help", "-h", "?"}
DRAFT_KEYWORDS = {"draft", "--draft"}


def is_help_request(args: str) -> bool:
    """Check if arguments are a help request per SKILL.md."""
    return args.strip().lower() in HELP_TRIGGERS if args and args.strip() else False


def parse_arguments(args: str) -> dict:
    """Parse ship-it arguments per SKILL.md.

    Returns:
        {"draft": bool, "title": str | None}
    """
    if not args or not args.strip():
        return {"draft": False, "title": None}

    stripped = args.strip()

    # Check for draft keyword at the start
    words = stripped.split(None, 1)
    if words[0].lower() in DRAFT_KEYWORDS:
        title = words[1].strip() if len(words) > 1 and words[1].strip() else None
        return {"draft": True, "title": title}

    return {"draft": False, "title": stripped}


def to_branch_name(title: str, change_type: str = "feat") -> str:
    """Convert a title to a branch name per SKILL.md Step 2.

    Applies kebab-case and prefixes with change type.
    """
    # Lowercase, replace non-alphanumeric with hyphens, collapse multiples
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return f"{change_type}/{slug}"
