"""Tests for jq filter snippets documented in bot-polling.md and SKILL.md.

These filters must avoid jq's ``!=`` operator because zsh escapes ``!``
in Bash arguments, turning ``!=`` into ``\\!=`` and causing parse errors.
The rewrites use ``(== | not)`` or ``(type == "string")`` instead.

Each test runs a copied jq filter expression corresponding to the skill
reference files against sample JSON to verify the rewrite produces the
expected output. Keep these constants in sync with the documented filters.
"""

import json
import subprocess


def run_jq(
    filter_expr: str,
    input_data: list | dict,
    args: dict | None = None,
    slurp: bool = True,
) -> list | dict:
    """Run a jq filter against input_data and return parsed output.

    When slurp=True (default), passes -s to mirror the ``| jq -s`` piping
    used in the skill's bash snippets. The input_data should already be
    structured as the skill would see it (e.g. a list of page arrays for
    paginated endpoints).
    """
    cmd = ["jq"]
    if slurp:
        cmd.append("-s")
    for k, v in (args or {}).items():
        cmd.extend(["--arg", k, v])
    cmd.append(filter_expr)
    result = subprocess.run(
        cmd,
        input=json.dumps(input_data),
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(result.stdout)


# --- Stale-HEAD bot detection (bot-polling.md) ---

STALE_HEAD_FILTER = (
    "[.[] | .[]]"
    ' | map(select((.user.login | endswith("[bot]"))'
    ' and (.user.login == "claude[bot]" | not)'
    ' and (.state == "PENDING" | not)'
    ' and (.submitted_at | type == "string")))'
    " | sort_by(.user.login)"
    " | group_by(.user.login)"
    " | map(sort_by(.submitted_at) | last)"
    " | map(select((.commit_id == $head_sha) | not))"
    " | map(.user.login)"
)

# Fixture simulates one page of paginated API output. With jq -s, this
# becomes [[...]], and the filter's [.[] | .[]] double-unwraps it.
STALE_HEAD_REVIEWS = [
    {"user": {"login": "copilot-pull-request-reviewer[bot]"}, "state": "COMMENTED", "submitted_at": "2026-04-01T10:00:00Z", "commit_id": "old111"},
    {"user": {"login": "copilot-pull-request-reviewer[bot]"}, "state": "COMMENTED", "submitted_at": "2026-04-02T10:00:00Z", "commit_id": "abc123"},
    {"user": {"login": "claude[bot]"}, "state": "COMMENTED", "submitted_at": "2026-04-01T10:00:00Z", "commit_id": "old111"},
    {"user": {"login": "claude-reviewer[bot]"}, "state": "COMMENTED", "submitted_at": "2026-04-01T10:00:00Z", "commit_id": "old333"},
    {"user": {"login": "dependabot[bot]"}, "state": "COMMENTED", "submitted_at": "2026-04-01T10:00:00Z", "commit_id": "old222"},
    {"user": {"login": "human-user"}, "state": "APPROVED", "submitted_at": "2026-04-01T10:00:00Z", "commit_id": "old111"},
    {"user": {"login": "pending-bot[bot]"}, "state": "PENDING", "submitted_at": None, "commit_id": None},
    {"user": {"login": "null-ts-bot[bot]"}, "state": "APPROVED", "submitted_at": None, "commit_id": None},
]


def test_stale_head_excludes_current_head():
    result = run_jq(STALE_HEAD_FILTER, STALE_HEAD_REVIEWS, {"head_sha": "abc123"})
    assert "copilot-pull-request-reviewer[bot]" not in result


def test_stale_head_excludes_claude():
    result = run_jq(STALE_HEAD_FILTER, STALE_HEAD_REVIEWS, {"head_sha": "abc123"})
    assert "claude[bot]" not in result


def test_stale_head_includes_claude_prefixed_bot():
    """A bot with 'claude' in its name but not exactly claude[bot] should be included."""
    result = run_jq(STALE_HEAD_FILTER, STALE_HEAD_REVIEWS, {"head_sha": "abc123"})
    assert "claude-reviewer[bot]" in result


def test_stale_head_excludes_pending():
    result = run_jq(STALE_HEAD_FILTER, STALE_HEAD_REVIEWS, {"head_sha": "abc123"})
    assert "pending-bot[bot]" not in result


def test_stale_head_excludes_null_submitted_at():
    """Non-PENDING bot with null submitted_at — tests the type guard independently."""
    result = run_jq(STALE_HEAD_FILTER, STALE_HEAD_REVIEWS, {"head_sha": "abc123"})
    assert "null-ts-bot[bot]" not in result


def test_stale_head_excludes_humans():
    result = run_jq(STALE_HEAD_FILTER, STALE_HEAD_REVIEWS, {"head_sha": "abc123"})
    assert "human-user" not in result


def test_stale_head_includes_stale_bots():
    result = run_jq(STALE_HEAD_FILTER, STALE_HEAD_REVIEWS, {"head_sha": "abc123"})
    assert "dependabot[bot]" in result


def test_stale_head_uses_latest_review():
    """Copilot has two reviews; the latest is on HEAD, so not stale."""
    result = run_jq(STALE_HEAD_FILTER, STALE_HEAD_REVIEWS, {"head_sha": "abc123"})
    assert result == ["claude-reviewer[bot]", "dependabot[bot]"]


# --- Post-fetch bot review detection (bot-polling.md Step 6c) ---
# This tests the Step 6c initial broad-match detection filter (any [bot]),
# distinct from Signal 2/3's per-bot equality filters tested below.

POST_FETCH_REVIEW_FILTER = (
    '[.[] | .[] | select((.user.login | endswith("[bot]"))'
    ' and (.submitted_at | type == "string")'
    " and .submitted_at >= $ts)]"
)


def test_post_fetch_includes_recent_bot():
    data = [
        {"user": {"login": "copilot-pull-request-reviewer[bot]"}, "submitted_at": "2026-04-01T13:00:00Z"},
        {"user": {"login": "copilot-pull-request-reviewer[bot]"}, "submitted_at": "2026-04-01T11:00:00Z"},
    ]
    result = run_jq(POST_FETCH_REVIEW_FILTER, data, {"ts": "2026-04-01T12:00:00Z"})
    assert len(result) == 1
    assert result[0]["submitted_at"] == "2026-04-01T13:00:00Z"


def test_post_fetch_excludes_humans():
    data = [
        {"user": {"login": "human-user"}, "submitted_at": "2026-04-01T14:00:00Z"},
    ]
    result = run_jq(POST_FETCH_REVIEW_FILTER, data, {"ts": "2026-04-01T12:00:00Z"})
    assert len(result) == 0


def test_post_fetch_excludes_null_submitted():
    data = [
        {"user": {"login": "bot-no-review[bot]"}, "submitted_at": None},
    ]
    result = run_jq(POST_FETCH_REVIEW_FILTER, data, {"ts": "2026-04-01T12:00:00Z"})
    assert len(result) == 0


# --- Signal 2 per-bot filter (bot-polling.md) ---
# bot-polling.md uses a <bot_login> placeholder in the jq filter; the test
# parameterizes it via --arg bot to validate the jq logic mechanically.

SIGNAL2_FILTER = (
    '[.[] | .[] | select(.user.login == $bot'
    ' and (.submitted_at | type == "string")'
    " and .submitted_at >= $ts)]"
)


def test_signal2_matches_specific_bot():
    data = [
        {"user": {"login": "copilot-pull-request-reviewer[bot]"}, "submitted_at": "2026-04-01T13:00:00Z"},
        {"user": {"login": "other-bot[bot]"}, "submitted_at": "2026-04-01T14:00:00Z"},
    ]
    result = run_jq(SIGNAL2_FILTER, data, {"bot": "copilot-pull-request-reviewer[bot]", "ts": "2026-04-01T12:00:00Z"})
    assert len(result) == 1
    assert result[0]["user"]["login"] == "copilot-pull-request-reviewer[bot]"


# --- Signal 3 per-bot timeline comment filter (bot-polling.md) ---
# Same parameterization note as Signal 2 above.

SIGNAL3_FILTER = (
    '[.[] | .[] | select(.user.login == $bot'
    ' and (.created_at | type == "string")'
    " and .created_at >= $ts)]"
)


def test_signal3_matches_specific_bot():
    data = [
        {"user": {"login": "copilot-pull-request-reviewer[bot]"}, "created_at": "2026-04-01T13:00:00Z"},
        {"user": {"login": "other-bot[bot]"}, "created_at": "2026-04-01T14:00:00Z"},
    ]
    result = run_jq(SIGNAL3_FILTER, data, {"bot": "copilot-pull-request-reviewer[bot]", "ts": "2026-04-01T12:00:00Z"})
    assert len(result) == 1
    assert result[0]["user"]["login"] == "copilot-pull-request-reviewer[bot]"


def test_signal3_excludes_old_comments():
    data = [
        {"user": {"login": "copilot-pull-request-reviewer[bot]"}, "created_at": "2026-04-01T11:00:00Z"},
    ]
    result = run_jq(SIGNAL3_FILTER, data, {"bot": "copilot-pull-request-reviewer[bot]", "ts": "2026-04-01T12:00:00Z"})
    assert len(result) == 0


# --- SKILL.md review body filter ---
# SKILL.md uses --jq '.[] | select(...)' (per-item output) piped to jq -s.
# The test collapses both steps into '[.[] | select(...)]' with slurp=False.

REVIEW_BODY_FILTER = (
    '[.[] | select((.state == "CHANGES_REQUESTED" or .state == "COMMENTED")'
    " and .body and (.body | length > 0))]"
)


def test_review_body_includes_changes_requested():
    data = [{"state": "CHANGES_REQUESTED", "body": "fix this"}]
    result = run_jq(REVIEW_BODY_FILTER, data, slurp=False)
    assert len(result) == 1


def test_review_body_excludes_approved():
    data = [{"state": "APPROVED", "body": "lgtm"}]
    result = run_jq(REVIEW_BODY_FILTER, data, slurp=False)
    assert len(result) == 0


def test_review_body_excludes_empty_body():
    data = [{"state": "COMMENTED", "body": ""}]
    result = run_jq(REVIEW_BODY_FILTER, data, slurp=False)
    assert len(result) == 0


def test_review_body_excludes_null_body():
    data = [{"state": "COMMENTED", "body": None}]
    result = run_jq(REVIEW_BODY_FILTER, data, slurp=False)
    assert len(result) == 0


# --- No != in filter strings (meta-test) ---


def test_no_bang_equals_in_filters():
    """All filter constants must avoid != for zsh portability."""
    for name, val in [
        ("STALE_HEAD_FILTER", STALE_HEAD_FILTER),
        ("POST_FETCH_REVIEW_FILTER", POST_FETCH_REVIEW_FILTER),
        ("SIGNAL2_FILTER", SIGNAL2_FILTER),
        ("SIGNAL3_FILTER", SIGNAL3_FILTER),
        ("REVIEW_BODY_FILTER", REVIEW_BODY_FILTER),
    ]:
        assert "!=" not in val, f"{name} contains != which breaks in zsh"


def test_no_bang_equals_in_source_files():
    """Source skill files must not contain != inside jq filter blocks."""
    from pathlib import Path

    repo_root = Path(__file__).resolve().parent.parent.parent
    source_files = [
        repo_root / "skills/pr-comments/references/bot-polling.md",
        repo_root / "skills/pr-comments/SKILL.md",
    ]
    for path in source_files:
        in_jq_block = False
        for lineno, line in enumerate(path.read_text().splitlines(), 1):
            if "| jq " in line.strip() or "--jq " in line.strip():
                in_jq_block = True
            elif line.strip().startswith("```") and in_jq_block:
                in_jq_block = False
            if in_jq_block and "!=" in line:
                raise AssertionError(
                    f"{path}:{lineno} contains != in jq filter: {line.strip()}"
                )
