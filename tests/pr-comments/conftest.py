"""Pytest fixtures for pr-comments skill tests."""

import re

HELP_TRIGGERS = {"help", "--help", "-h", "?"}

# SKILL.md Step 1 / Arguments validation regexes (spec 39):
# - explicitly-supplied PR number (after stripping a single leading '#' and
#   surrounding whitespace) must match PR_NUMBER_RE before any shell call;
# - any --max N (and backward-compatible --auto N) value must match MAX_VALUE_RE.
PR_NUMBER_RE = re.compile(r"^[1-9][0-9]{0,5}$")
MAX_VALUE_RE = re.compile(r"^[1-9][0-9]{0,3}$")


def validate_pr_number(value: str) -> bool:
    """Return True if value is a valid PR number per SKILL.md Step 1.

    Strips surrounding whitespace, then a single leading ``#`` (so ``42``,
    ``#42``, and ``  42  `` are all accepted), then matches against
    ``PR_NUMBER_RE`` (``^[1-9][0-9]{0,5}$`` — rejects ``0`` and
    unbounded-length digit strings).
    """
    if value is None:
        return False
    cleaned = str(value).strip().removeprefix("#")
    return bool(PR_NUMBER_RE.match(cleaned))


def validate_max_value(value: str) -> bool:
    """Return True if value is a valid ``--max N`` (or ``--auto N``) per SKILL.md.

    Strips surrounding whitespace, then matches against ``MAX_VALUE_RE``
    (``^[1-9][0-9]{0,3}$`` — 1–9999, well above any realistic loop cap).
    """
    if value is None:
        return False
    return bool(MAX_VALUE_RE.match(str(value).strip()))


def is_help_request(args: str) -> bool:
    """Check if arguments are a help request per SKILL.md."""
    return args.strip().lower() in HELP_TRIGGERS if args and args.strip() else False


def is_pr_number(args: str) -> bool:
    """Check if arguments are a PR number per SKILL.md.

    Strips a leading '#' before checking (e.g. '#42' → '42'). Delegates to
    :func:`validate_pr_number` so the suite models the spec-39 regex
    (``^[1-9][0-9]{0,5}$``) rather than the looser ``isdigit()`` check.
    """
    return bool(args) and validate_pr_number(args)


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
    """Parse mode flags from arguments per SKILL.md.

    Auto mode is the default. ``--manual`` restores the confirmation gate, and
    is **sticky** — once ``--manual`` appears anywhere in the arguments the
    invocation is manual regardless of token order; ``--auto`` never flips it
    back (``--auto`` is a no-op alias retained only for legacy callers, since
    auto is already the default).
    ``--max N`` sets the iteration cap; ``--auto [N]`` is accepted for backward
    compatibility (``--auto N`` is treated as ``--max N``). A following integer
    token is consumed by ``--max`` / ``--auto`` so it cannot leak into
    ``remaining_args`` (e.g., ``"0"`` being misparsed as PR #0).

    Mirrors the SKILL.md Step 1 / Arguments rules:

    - ``--manual`` wins whenever present; ``--auto`` does not override it.
    - ``--max`` / ``--auto N`` are **ignored in manual mode** — manual mode has
      no auto-loop to cap, so a supplied value is consumed but discarded without
      use; it never reaches a shell call or a loop bound, so it is neither
      validated nor an error (SKILL.md scopes the ``--max`` validation
      requirement to auto mode for exactly this reason).
    - In auto mode a supplied integer value must pass :func:`validate_max_value`
      (1–9999) before the loop cap is applied; anything else (``--max 0``,
      ``--max 01``, ``--max 10000``) raises ``ValueError`` rather than being
      silently dropped, matching the doc's ``Invalid --max value: <value>.
      Must be a positive integer.`` stop.

    Returns:
        {
            "auto": bool,
            "max_iterations": int,
            "remaining_args": str,
        }
    where auto defaults to True, max_iterations defaults to 10,
    and remaining_args is the original args with any mode flag tokens removed.

    Raises:
        ValueError: if an invalid ``--max`` / ``--auto N`` value is supplied
            in auto mode.
    """
    if not args or not args.strip():
        return {"auto": True, "max_iterations": 10, "remaining_args": ""}

    tokens = args.strip().split()
    manual_seen = False  # --manual is sticky for the whole invocation
    max_iterations = 10
    requested_max: str | None = None  # last --max / --auto numeric value seen
    remaining_tokens: list[str] = []

    i = 0
    while i < len(tokens):
        if tokens[i] == "--manual":
            manual_seen = True
            i += 1
        elif tokens[i] in ("--auto", "--max"):
            # --auto is a no-op alias (auto is the default) and never re-enables
            # auto mode once --manual has been seen — manual is sticky.
            # Consume a following integer token so it cannot leak into
            # remaining_args; whether it is *applied* is decided after the loop.
            if i + 1 < len(tokens) and tokens[i + 1].isdigit():
                requested_max = tokens[i + 1]
                i += 2
            else:
                i += 1
        else:
            remaining_tokens.append(tokens[i])
            i += 1

    auto = not manual_seen
    # --max / --auto N are ignored in manual mode; in auto mode an invalid
    # value is a hard error rather than a silent no-op.
    if auto and requested_max is not None:
        if not validate_max_value(requested_max):
            raise ValueError(
                f"Invalid --max value: {requested_max}. Must be a positive integer."
            )
        max_iterations = int(requested_max)

    return {
        "auto": auto,
        "max_iterations": max_iterations,
        "remaining_args": " ".join(remaining_tokens),
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
    bot_timeline_after_fetch: list[dict] | None = None,
    stale_head_bots: list[str] | None = None,
) -> bool:
    """Returns True if the repoll gate (Step 6c) should trigger.

    Per SKILL.md Step 6c: when every plan item is `skip` (or the plan is empty)
    and bot reviewers are pending, have submitted a review/timeline comment after
    fetch_timestamp, or have not yet reviewed the current HEAD commit, the skill
    should re-poll rather than exiting.

    Requires every item's action to be exactly ``skip`` — unknown or missing
    action values do not count as skip and will prevent the repoll gate from
    firing.

    ``bot_reviews_after_fetch`` may be ``None`` or a pre-filtered list of
    bot-authored reviews (entries with ``submitted_at`` set).
    ``bot_timeline_after_fetch`` may be ``None`` or a pre-filtered list of
    bot-authored timeline comments (entries with ``created_at`` set).
    ``stale_head_bots`` may be ``None`` or a pre-filtered list of bot logins
    whose most recent submitted review was on an older commit (excludes
    ``claude[bot]`` and PENDING reviews). When provided, the caller is
    responsible for pre-filtering in all cases.
    """
    if plan_items and not all(item.get("action") == "skip" for item in plan_items):
        return False

    has_pending_bots = len(pending_bots) > 0
    has_recent_bot_review = bool(bot_reviews_after_fetch)
    has_recent_bot_timeline = bool(bot_timeline_after_fetch)
    has_stale_head_bots = bool(stale_head_bots)

    return (
        has_pending_bots
        or has_recent_bot_review
        or has_recent_bot_timeline
        or has_stale_head_bots
    )


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
    """Returns True if any Step 6b consistency item forces manual confirmation.

    Per SKILL.md Step 7, Step 6b `consistency` items always require manual
    confirmation even in auto-mode. Step 9 drift rows (source="9") do NOT
    trigger this escalation — they are auto-applied without confirmation.

    Items without a `source` field default to Step 6b behavior.
    """
    return any(
        item.get("action") == "consistency" and item.get("source", "6b") != "9"
        for item in plan_items
    )


# ---------------------------------------------------------------------------
# Step 9 helpers: post-edit drift re-scan
# ---------------------------------------------------------------------------

def is_nontrivial_substring(s: str) -> bool:
    """Returns True if a replaced substring is worth scanning for in siblings.

    Per SKILL.md Step 9, a substring is non-trivial if any of:
    - length >= 20 characters
    - starts with '--' (CLI flag, e.g. --body-file)
    - contains '/' followed by a non-space character (file path or URL)

    Pure whitespace changes, single-word tweaks, and numeric-only changes
    are excluded.
    """
    if not s or not s.strip():
        return False
    s = s.strip()
    if s.isdigit():
        return False
    if s.startswith("--"):
        return True
    if "/" in s and any(not c.isspace() for c in s.split("/", 1)[1][:1]):
        return True
    return len(s) >= 20


def find_drift_rows(
    replacements: list[tuple[str, str]],
    pr_files: dict[str, str],
) -> list[dict]:
    """Find sibling references still using the old text after Step 8 edits.

    Args:
        replacements: list of (old_text, new_text) pairs from Step 8 edits.
            Only non-trivial old_text values are scanned (per is_nontrivial_substring).
        pr_files: mapping of {filename: file_content} for PR-modified files.

    Returns:
        list of {"file": str, "old": str} for each genuine match found.
        Empty list means no drift — silent on clean.

    CLI flag matching uses word-boundary semantics: `--body` does not match
    within `--body-file`. A CLI flag match requires the flag to be followed
    by a non-flag character (space, quote, newline, end of string) so that
    flag prefixes don't produce false positives.
    """
    rows = []
    for old_text, _new_text in replacements:
        if not is_nontrivial_substring(old_text):
            continue
        for filename, content in pr_files.items():
            if _text_present(old_text, content):
                rows.append({"file": filename, "old": old_text})
    return rows


def _text_present(needle: str, haystack: str) -> bool:
    """Return True if needle appears in haystack.

    For CLI flags (starting with '--'), uses boundary-aware matching: requires
    the match is not immediately followed by a word character or '-', so
    '--body' does not match inside '--body-file'.

    For all other strings, uses plain substring matching (needle in haystack).
    """
    if needle.startswith("--"):
        pattern = re.escape(needle) + r"(?![\w-])"
        return bool(re.search(pattern, haystack))
    return needle in haystack


# ---------------------------------------------------------------------------
# Step 6 helpers: convention-rule sanity-check
# ---------------------------------------------------------------------------

_CONVENTION_FILE_PATTERNS = (
    "CLAUDE.md",
    "AGENTS.md",
    "copilot-instructions.md",
)

_NORMATIVE_PATTERNS = (
    r"\bmust\b",
    r"\balways\b",
    r"\bconvention requires\b",
    r"\bconvention is\b",
    r"\bshould always\b",
    r"\ball .{0,40} must\b",
    r"\ball .{0,40} should\b",
)


def is_convention_file(path: str) -> bool:
    """Returns True if the file path targets a conventions/instructions file.

    Per SKILL.md Step 6, the check applies to CLAUDE.md,
    .github/copilot-instructions.md, AGENTS.md, or any file whose basename
    matches *instructions*.md or *CLAUDE*.md.
    """
    basename = path.split("/")[-1] if "/" in path else path
    for pattern in _CONVENTION_FILE_PATTERNS:
        if basename == pattern:
            return True
    if "instructions" in basename and basename.endswith(".md"):
        return True
    if "CLAUDE" in basename and basename.endswith(".md"):
        return True
    return False


def has_normative_language(body: str) -> bool:
    """Returns True if the comment body proposes a universal rule.

    Detects normative language patterns that suggest the reviewer is proposing
    a mandatory convention ("must", "always", "convention requires", etc.).
    """
    for pattern in _NORMATIVE_PATTERNS:
        if re.search(pattern, body, re.IGNORECASE):
            return True
    return False


def triggers_convention_sanity_check(comment: dict) -> bool:
    """Returns True if Step 6 should run the convention sanity-check for this comment.

    Triggers when:
    - The comment targets a conventions/instructions file, AND
    - The body proposes a rule using normative language.
    """
    path = comment.get("path", "")
    body = comment.get("body", "")
    return is_convention_file(path) and has_normative_language(body)


def classify_convention_suggestion(
    counter_example_count: int,
    can_soften: bool,
) -> dict:
    """Classify a convention-rule suggestion after counter-example search.

    Per SKILL.md Step 6 convention sanity-check:
    - 0-1 counter-examples: fix normally (rule is consistent with repo)
    - >=2, can soften: fix with softened wording (preference not mandate)
    - >=2, cannot soften: decline with counter-example evidence

    Returns:
        {"action": str, "softened": bool}
        where softened=True means the wording should be loosened to a preference.
    """
    if counter_example_count <= 1:
        return {"action": "fix", "softened": False}
    if can_soften:
        return {"action": "fix", "softened": True}
    return {"action": "decline", "softened": False}


def _nonwhitespace_prefix(body: str, length: int = 200) -> str:
    """Return first `length` non-whitespace characters of body."""
    return re.sub(r"\s+", "", body)[:length]


def filter_timeline_comments(
    timeline_comments: list[dict],
    pr_author: str,
    auth_user: str,
    review_body_comments: list[dict],
) -> list[dict]:
    """Filter raw timeline comments per Step 2c rules.

    Applies three filters in order:
    1. Exclude comments by the PR author.
    2. Exclude comments by the authenticated user (prior skill replies).
    3. Dedup against review body comments: discard a timeline comment if its
       author matches a review body comment's author AND their first 200
       non-whitespace characters match.

    Returns the filtered list.
    """
    result = []
    for tc in timeline_comments:
        author = tc.get("author", "")
        if author == pr_author:
            continue
        if author == auth_user:
            continue
        # Dedup: check against review body comments from the same author
        tc_prefix = _nonwhitespace_prefix(tc.get("body", ""))
        duplicate = False
        for rb in review_body_comments:
            if rb.get("author") == author:
                rb_prefix = _nonwhitespace_prefix(rb.get("body", ""))
                if tc_prefix == rb_prefix:
                    duplicate = True
                    break
        if not duplicate:
            result.append(tc)
    return result


def is_already_addressed(
    comment: dict,
    all_timeline_comments: list[dict],
    pr_author: str,
    auth_user: str,
) -> bool:
    """Return True if a timeline comment is already addressed.

    Per Step 2c: a timeline comment is considered already addressed only if a
    later timeline comment (by created_at) from the PR author or authenticated
    user either (a) @mentions the original commenter's login, or (b) quotes
    some of their text in a blockquote — a ``>`` line whose non-empty content
    appears in the original comment's body. A plain unrelated follow-up does
    not count.

    Note:
        ``all_timeline_comments`` must be the full, unfiltered timeline as
        returned by the GitHub API. In particular, do not pass in the result
        of :func:`filter_timeline_comments` (or any other list that removes
        comments from the PR author or authenticated user), otherwise this
        function will never see the addressing replies and will return False
        incorrectly.
    """
    commenter = comment.get("author", "")
    comment_time = comment.get("created_at", "")

    for later in all_timeline_comments:
        later_author = later.get("author", "")
        later_time = later.get("created_at", "")
        if later_author not in (pr_author, auth_user):
            continue
        if later_time <= comment_time:
            continue
        body = later.get("body", "")
        # Check for @mention with GitHub-username boundaries so that
        # "@alice" does not match within "@alice2" or an email/URL.
        if commenter:
            mention_pattern = rf"(?<![A-Za-z0-9-])@{re.escape(commenter)}(?![A-Za-z0-9-])"
            if re.search(mention_pattern, body):
                return True
        # Check for a blockquote that quotes the original comment's text.
        # A bare ">" with no matching content does not count — the quoted
        # line must overlap with the original comment's body.
        original_body = comment.get("body", "")
        for line in body.splitlines():
            if line.startswith(">"):
                quoted = line[1:].strip()
                if quoted and quoted in original_body:
                    return True
    return False


def should_signal3_fire(new_bot_timeline_comments: list[dict]) -> bool:
    """Return True if Signal 3 should trigger a loop-back to Step 2.

    Per bot-polling.md Signal 3: fires when a polled bot has posted a new
    timeline comment since snapshot_timestamp.
    """
    return len(new_bot_timeline_comments) > 0


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
