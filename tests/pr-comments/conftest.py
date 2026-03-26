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


def parse_auto_flag(args: str) -> dict:
    """Parse the --auto [N] flag from arguments per SKILL.md.

    Returns:
        {
            "auto": bool,
            "max_iterations": int,
            "remaining_args": str,
        }
    where max_iterations defaults to 10 if --auto is present without N,
    and remaining_args is the original args with any --auto [N] tokens removed.
    """
    if not args or not args.strip():
        return {"auto": False, "max_iterations": 10, "remaining_args": ""}

    tokens = args.strip().split()
    auto = False
    max_iterations = 10
    remaining_tokens: list[str] = []

    i = 0
    while i < len(tokens):
        if tokens[i] == "--auto":
            auto = True
            # Consume any non-negative integer following --auto to prevent it
            # from leaking into remaining_args (e.g., "0" being misparsed as PR #0).
            # Only positive values are used as the iteration cap.
            if i + 1 < len(tokens) and tokens[i + 1].isdigit():
                if int(tokens[i + 1]) > 0:
                    max_iterations = int(tokens[i + 1])
                i += 2
            else:
                i += 1
        else:
            remaining_tokens.append(tokens[i])
            i += 1

    remaining_args = " ".join(remaining_tokens)
    return {
        "auto": auto,
        "max_iterations": max_iterations,
        "remaining_args": remaining_args,
    }


def should_exit_auto_loop(
    iteration: int,
    max_iterations: int,
    new_threads: int,
    polled_bots_remaining: int = 0,
) -> bool:
    """Returns True if the auto-loop should exit before starting the next iteration.

    `iteration` is the 1-indexed count of the just-completed iteration (e.g.
    iteration=3 means 3 rounds have finished). The loop exits when iteration
    equals max_iterations, preventing a further iteration from starting.

    `polled_bots_remaining` is the count of bots being polled that have NOT yet
    submitted a review (per Signal 2 tracking). When bots are still outstanding,
    the loop continues even if no new threads appeared in this cycle.

    bot-polling.md defines four exit conditions (including timeout and
    security-screening/manual-confirmation), but this helper only models the
    subset that can be expressed via its parameters:
    - Exit when no new threads AND all polled bots have responded (remaining=0)
    - Exit when iteration count has reached the maximum

    Timeout-based and security/manual-confirmation exits are enforced elsewhere
    and are intentionally not represented in this helper.
    """
    if iteration >= max_iterations:
        return True
    if new_threads == 0 and polled_bots_remaining == 0:
        return True
    return False


def should_repoll_on_all_skip(
    plan_items: list[dict],
    pending_bots: list[str],
    bot_reviews_after_fetch: list[dict] | None = None,
) -> bool:
    """Returns True if the repoll gate (Step 6c) should trigger.

    Per SKILL.md Step 6c: when every plan item is `skip` (or the plan is empty)
    and bot reviewers are pending or submitted a review after fetch_timestamp,
    the skill should re-poll rather than exiting.

    Requires every item's action to be exactly ``skip`` — unknown or missing
    action values do not count as skip and will prevent the repoll gate from
    firing.
    """
    if plan_items and not all(item.get("action") == "skip" for item in plan_items):
        return False

    has_pending_bots = len(pending_bots) > 0
    has_recent_bot_review = bool(bot_reviews_after_fetch)

    return has_pending_bots or has_recent_bot_review


def should_repoll_guard_allow(
    last_all_skip_happened: bool,
    last_all_skip_bot_set: set[str] | None,
    current_bot_set: set[str],
) -> bool:
    """Returns True if the rapid re-poll guard allows an immediate re-fetch.

    Per SKILL.md Step 6c rapid re-poll guard:
    - First all-skip → allow immediate re-fetch
    - Second consecutive all-skip with same bot set → block (use 60s polling)
    - Bot set changed → allow immediate re-fetch
    """
    if not last_all_skip_happened:
        return True
    if last_all_skip_bot_set is not None and current_bot_set == last_all_skip_bot_set:
        return False
    return True


def requires_manual_confirmation(plan_items: list[dict]) -> bool:
    """Returns True if any item in the plan forces manual confirmation.

    Per SKILL.md Step 7, `consistency` items always require manual confirmation
    even in auto-mode. This helper only models the consistency-based trigger.
    """
    manual_triggers = {"consistency"}
    return any(item.get("action") in manual_triggers for item in plan_items)


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
