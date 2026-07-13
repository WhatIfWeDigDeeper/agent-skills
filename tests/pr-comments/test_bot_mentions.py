"""
Tests for bot-mention suppression in posted content (spec 52):
- is_bot_author: user.type == "Bot" is primary; [bot] suffix is fallback
- bot_display_name: Bot Display Names algorithm (references/bot-polling.md)
- commenter_ref: "@alice" for humans, bare handle for bots
- No skill file emits a live @-mention of a known bot
"""

import re
from pathlib import Path

from conftest import bot_display_name, commenter_ref, is_bot_author

SKILL_DIR = Path(__file__).resolve().parents[2] / "skills" / "pr-comments"

KNOWN_BOT_HANDLES = ["copilot", "claude", "coderabbitai", "gemini", "renovate", "dependabot"]
BOT_MENTION_MARKER = "<!-- bot-mention-example -->"
_BOT_MENTION_PATTERN = re.compile(r"@(" + "|".join(KNOWN_BOT_HANDLES) + r")\b", re.IGNORECASE)


def _scan_lines_for_bot_mentions(lines: list[str]) -> list[int]:
    """Return 1-indexed line numbers that contain a live `@`-mention of a known bot.

    Any line containing the literal marker `<!-- bot-mention-example -->` is
    skipped, even if it also matches the bot-mention pattern. The marker exists
    so documentation prose can show the concrete anti-example (e.g. "never
    write: Good catch @Copilot") that the guard otherwise exists to catch —
    mirroring `<!-- cspell:disable-line -->` for intentional non-ASCII text.

    Only use this marker on documentation prose lines. Never add it to a
    template body: templates are interpolated and posted verbatim, so marking
    one would let a real `@`-mention slip through into a posted GitHub comment.
    """
    offenders = []
    for lineno, line in enumerate(lines, 1):
        if BOT_MENTION_MARKER in line:
            continue
        if _BOT_MENTION_PATTERN.search(line):
            offenders.append(lineno)
    return offenders


class TestIsBotAuthor:
    def test_type_bot_is_bot_even_without_suffix(self):
        """Copilot on /pulls/{n}/comments has login 'Copilot' and no [bot] suffix."""
        assert is_bot_author({"login": "Copilot", "type": "Bot"}) is True

    def test_bot_suffix_is_bot_when_type_missing(self):
        assert is_bot_author({"login": "coderabbitai[bot]"}) is True

    def test_human_is_not_bot(self):
        assert is_bot_author({"login": "alice", "type": "User"}) is False

    def test_human_without_type_is_not_bot(self):
        assert is_bot_author({"login": "alice"}) is False

    def test_human_login_containing_bot_substring_is_not_bot(self):
        """'botany' must not be misread as a bot."""
        assert is_bot_author({"login": "botany", "type": "User"}) is False


class TestBotDisplayName:
    def test_strips_bot_suffix(self):
        assert bot_display_name("renovate[bot]") == "renovate"

    def test_takes_first_hyphen_token(self):
        assert bot_display_name("copilot-pull-request-reviewer[bot]") == "copilot"

    def test_bare_login_unchanged(self):
        assert bot_display_name("Copilot") == "Copilot"

    def test_claude_bot(self):
        assert bot_display_name("claude[bot]") == "claude"


class TestCommenterRef:
    def test_human_keeps_at_mention(self):
        """@ on a human is their only notification on the flat PR timeline."""
        assert commenter_ref({"login": "alice", "type": "User"}) == "@alice"

    def test_bot_gets_bare_handle(self):
        """@copilot in a PR comment is a command, not a notification."""
        assert commenter_ref({"login": "Copilot", "type": "Bot"}) == "Copilot"

    def test_suffixed_bot_gets_bare_handle(self):
        assert commenter_ref({"login": "copilot-pull-request-reviewer[bot]", "type": "Bot"}) == "copilot"

    def test_no_bot_ref_ever_starts_with_at(self):
        bots = [
            {"login": "Copilot", "type": "Bot"},
            {"login": "claude[bot]", "type": "Bot"},
            {"login": "coderabbitai[bot]", "type": "Bot"},
            {"login": "gemini-code-assist[bot]", "type": "Bot"},
        ]
        for bot in bots:
            assert not commenter_ref(bot).startswith("@")


class TestSkillFilesHaveNoLiveBotMentions:
    """No posted-body template may @-mention a raw login, which expands to @Copilot for a bot."""

    KNOWN_BOT_HANDLES = KNOWN_BOT_HANDLES

    def _skill_md_files(self) -> list[Path]:
        return sorted(SKILL_DIR.rglob("*.md"))

    def _scan(self, predicate) -> list[str]:
        offenders = []
        for md in self._skill_md_files():
            for lineno, line in enumerate(md.read_text().splitlines(), 1):
                if predicate(line):
                    offenders.append(f"{md.relative_to(SKILL_DIR)}:{lineno}: {line.strip()}")
        return offenders

    def test_no_at_prefixed_login_placeholder(self):
        """`@{commenter_login}` expands to `@Copilot` for a bot commenter.

        This is how the `@` actually reached the posted body — not a hardcoded
        `@Copilot` literal. Templates must use `{commenter_ref}`, which drops
        the `@` for bots.
        """
        offenders = self._scan(lambda line: "@{commenter_login}" in line)
        assert offenders == [], (
            "Template @-mentions a raw login (expands to @Copilot for a bot); "
            "use {commenter_ref}:\n" + "\n".join(offenders)
        )

    def test_commenter_ref_is_defined(self):
        text = (SKILL_DIR / "references" / "reply-formats.md").read_text()
        assert "{commenter_ref}" in text
        assert "Referring to the commenter" in text

    def test_no_hardcoded_at_mention_of_known_bot(self):
        """Belt-and-braces: no literal `@Copilot` anywhere in skill content.

        A line is exempt only if it carries the literal marker
        `<!-- bot-mention-example -->` (see `_scan_lines_for_bot_mentions`),
        which lets documentation prose show the concrete anti-example the
        model must never write. This marker is for documentation prose only —
        never place it in a template body, since a template is interpolated
        and posted verbatim and the marker would suppress the exact literal
        this guard exists to catch.
        """
        offenders = []
        for md in self._skill_md_files():
            lines = md.read_text().splitlines()
            for lineno in _scan_lines_for_bot_mentions(lines):
                offenders.append(f"{md.relative_to(SKILL_DIR)}:{lineno}: {lines[lineno - 1].strip()}")
        assert offenders == [], "Live @-mention of a bot in skill content:\n" + "\n".join(offenders)


class TestBotMentionMarker:
    """Proves `<!-- bot-mention-example -->` suppresses only the line it's on."""

    def test_unmarked_mention_is_flagged(self):
        assert _scan_lines_for_bot_mentions(["Never write: Good catch @Copilot"]) == [1]

    def test_marked_mention_is_not_flagged(self):
        lines = [f"Never write: Good catch @Copilot {BOT_MENTION_MARKER}"]
        assert _scan_lines_for_bot_mentions(lines) == []

    def test_marker_does_not_suppress_other_lines(self):
        """The marker is not a blanket escape hatch — it only exempts its own line."""
        lines = [
            f"Never write: Good catch @Copilot {BOT_MENTION_MARKER}",
            "Also bad: @Copilot thanks",
        ]
        assert _scan_lines_for_bot_mentions(lines) == [2]


class TestBotTimelineNitSelfTermination:
    """A bot nit reply has no @-mention, so the '>' quote is its only linkage signal."""

    def _c(self, author: str, body: str, created_at: str) -> dict:
        return {"author": author, "body": body, "created_at": created_at}

    def test_bot_reply_without_at_mention_links_via_quote(self):
        from conftest import is_already_addressed

        nit = self._c("Copilot", "nit: rename `tmp` to `filtered`.", "2026-01-01T10:00:00Z")
        # The Task 2 template: bare handle, no "@", plus the mandatory '>' quote.
        reply = self._c(
            "skillbot",
            "Copilot\n> nit: rename `tmp` to `filtered`.\n\nNoted as a nit — leaving as-is for now.",
            "2026-01-01T11:00:00Z",
        )
        assert is_already_addressed(nit, [nit, reply], pr_author="prowner", auth_user="skillbot") is True

    def test_bot_reply_without_quote_does_not_link(self):
        """Dropping the quote on a bot reply loses the only linkage signal — it re-surfaces."""
        from conftest import is_already_addressed

        nit = self._c("Copilot", "nit: rename `tmp` to `filtered`.", "2026-01-01T10:00:00Z")
        reply = self._c(
            "skillbot",
            "Copilot\n\nNoted as a nit — leaving as-is for now.",
            "2026-01-01T11:00:00Z",
        )
        assert is_already_addressed(nit, [nit, reply], pr_author="prowner", auth_user="skillbot") is False

    def test_human_reply_still_links_via_at_mention_alone(self):
        """The human path is unchanged: @mention alone suffices, no quote needed."""
        from conftest import is_already_addressed

        comment = self._c("alice", "Please add tests.", "2026-01-01T10:00:00Z")
        reply = self._c("skillbot", "@alice tests added, see latest commit.", "2026-01-01T11:00:00Z")
        assert is_already_addressed(comment, [comment, reply], pr_author="prowner", auth_user="skillbot") is True
