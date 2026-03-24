"""Pytest fixtures for pr-comments skill tests."""

import re

HELP_TRIGGERS = {"help", "--help", "-h", "?"}


def is_help_request(args: str) -> bool:
    """Check if arguments are a help request per SKILL.md."""
    return args.strip().lower() in HELP_TRIGGERS if args and args.strip() else False


def is_pr_number(args: str) -> bool:
    """Check if arguments are a PR number per SKILL.md.

    Strips a leading '#' before checking (e.g. '#42' → '42').
    """
    if not args:
        return False
    stripped = args.strip().removeprefix("#")
    return bool(stripped and stripped.isdigit())


def parse_pr_argument(args: str) -> dict:
    """Parse the optional PR number argument per SKILL.md.

    Returns:
        {"type": "help"} if help trigger
        {"type": "pr_number", "number": int} if numeric
        {"type": "detect"} if empty/whitespace (detect from branch)
    """
    if not args or not args.strip():
        return {"type": "detect"}
    stripped = args.strip()
    if is_help_request(stripped):
        return {"type": "help"}
    if is_pr_number(stripped):
        cleaned = stripped.removeprefix("#")
        return {"type": "pr_number", "number": int(cleaned)}
    return {"type": "detect"}


def classify_comment(comment: dict) -> str:
    """Classify a review comment per SKILL.md Steps 4a and 5.

    Returns:
        "suggestion" if body contains a ```suggestion block
        "reply" if in_reply_to_id is set (not a top-level comment)
        "regular" otherwise
    """
    if comment.get("in_reply_to_id") is not None:
        return "reply"
    body = comment.get("body", "")
    if extract_suggestion_content(body) is not None:
        return "suggestion"
    return "regular"


def extract_suggestion_content(body: str) -> str | None:
    """Extract the content of a ```suggestion block from a comment body.

    Per SKILL.md Step 8, the content between ```suggestion and ``` is
    the exact replacement for the highlighted lines.
    """
    match = re.search(r"```suggestion\b[^\n]*\n(.*?)```", body, re.DOTALL)
    if match:
        return match.group(1)
    return None


def build_reviewer_list(
    implemented_comments: list[dict],
    declined_comments: list[dict],
    replied_comments: list[dict] | None = None,
) -> list[str]:
    """Build deduplicated reviewer list for push+re-request step.

    Per SKILL.md Step 13, collects from three sources:
    - implemented/accepted comments (Co-authored-by credit)
    - declined comments (received a reply)
    - replied comments (clarifying questions answered, thread left open)
    """
    all_comments = implemented_comments + declined_comments + (replied_comments or [])
    return extract_coauthors(all_comments)


def is_bot_login(login: str) -> bool:
    """Returns True if the login belongs to a bot account (has '[bot]' suffix)."""
    return login.endswith("[bot]")


def split_human_bot(reviewers: list[str]) -> tuple[list[str], list[str]]:
    """Split reviewer list into (humans, bots)."""
    humans = [r for r in reviewers if not is_bot_login(r)]
    bots = [r for r in reviewers if is_bot_login(r)]
    return humans, bots


def should_offer_poll(bot_reviewers: list[str]) -> bool:
    """Returns True if the poll prompt should be offered after re-requesting review.

    Per SKILL.md Step 13: only offer when at least one bot reviewer was re-requested.
    """
    return len(bot_reviewers) > 0


def extract_coauthors(comments: list[dict]) -> list[str]:
    """Extract unique comment authors for Co-authored-by trailers.

    Per SKILL.md Step 10, deduplicate — one entry per person.
    """
    authors = []
    seen = set()
    for comment in comments:
        author = comment.get("author", "")
        if author and author not in seen:
            seen.add(author)
            authors.append(author)
    return sorted(authors)
