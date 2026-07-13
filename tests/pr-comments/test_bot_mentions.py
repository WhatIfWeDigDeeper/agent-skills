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

    KNOWN_BOT_HANDLES = ["copilot", "claude", "coderabbitai", "gemini", "renovate", "dependabot"]

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
        """Belt-and-braces: no literal `@Copilot` anywhere in skill content."""
        pattern = re.compile(r"@(" + "|".join(self.KNOWN_BOT_HANDLES) + r")\b", re.IGNORECASE)
        offenders = self._scan(lambda line: bool(pattern.search(line)))
        assert offenders == [], "Live @-mention of a bot in skill content:\n" + "\n".join(offenders)
