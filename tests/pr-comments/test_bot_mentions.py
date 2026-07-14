"""
Tests for bot-mention suppression in posted content (spec 52):
- is_bot_author: user.type == "Bot" is primary; [bot] suffix is fallback
- bot_display_name: Bot Display Names algorithm (references/bot-polling.md)
- commenter_ref: "@alice" for humans, bare handle for bots
- No skill file emits a live @-mention of a known bot
"""

import re
from pathlib import Path

from conftest import bot_display_name, commenter_ref, is_already_addressed, is_bot_author

SKILL_DIR = Path(__file__).resolve().parents[2] / "skills" / "pr-comments"

KNOWN_BOT_HANDLES = [
    "copilot",
    "claude",
    "codecov",
    "coderabbitai",
    "gemini",
    "github-actions",
    "renovate",
    "dependabot",
    "sonarcloud",
]
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
        """`@{commenter_login}` (or any other `@{placeholder}`) expands to `@Copilot`
        for a bot commenter.

        This is how the `@` actually reached the posted body — not a hardcoded
        `@Copilot` literal. A future template written as `@{login}` or `@{author}`
        is the same bug under a different placeholder name, so match any
        `@{` immediately followed by a placeholder identifier, not just the
        literal `@{commenter_login}` spelling. Templates must use bare
        `{commenter_ref}` (no leading `@`), which drops the `@` for bots.
        """
        offenders = self._scan(lambda line: re.search(r"@\{[a-zA-Z_]+\}", line))
        assert offenders == [], (
            "Template @-mentions a raw placeholder (expands to @Copilot for a bot); "
            "use {commenter_ref}:\n" + "\n".join(offenders)
        )

    def test_reply_templates_use_commenter_ref_and_cite_the_rule(self):
        """reply-formats.md hosts the templates; commenter-ref.md hosts the rule.

        The templates interpolate `{commenter_ref}`, so the file that carries them
        must keep pointing at the file that defines it — otherwise the placeholder
        is filled in from memory, which is how the `@` got out.
        """
        text = (SKILL_DIR / "references" / "reply-formats.md").read_text()
        assert "{commenter_ref}" in text
        assert "references/commenter-ref.md" in text

    def test_commenter_ref_never_seeded_with_an_at_prefixed_literal(self):
        """A `commenter_ref` assignment must not model the `@`-prefixed human form.

        `commenter_ref` is *defined* as "@alice for a human, bare handle for a
        bot". Seeding it in an example with a hardcoded `@`-prefixed literal
        (`commenter_ref="@reviewer"`) models the human shape as the default in a
        snippet the agent fills in by substitution — so a bot commenter copied
        into it reintroduces the live `@`-mention this whole skill exists to
        prevent. Assign the `{commenter_ref}` placeholder instead, matching the
        `{owner}`/`{repo}` convention used elsewhere in the same snippet.

        Deliberately narrow — anchored to a shell *assignment*, so it cannot fire
        on prose. Explanatory text that documents the human mapping (`# commenter_ref:
        "@alice" for a human...`) is correct and must stay legal, `@reviewer` is a
        legitimate *human* placeholder throughout the evals (eval 35 asserts a reply
        body starts with `@reviewer`), and terminal-only prompts keep their `@` too.
        """
        offenders = self._scan(
            lambda line: re.match(r"""\s*commenter_ref\s*=\s*["']?@""", line)
        )
        assert offenders == [], (
            "`commenter_ref` is seeded with an @-prefixed literal; for a bot commenter "
            'that posts a live @-mention. Use commenter_ref="{commenter_ref}":\n'
            + "\n".join(offenders)
        )

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


class TestCommenterRefRuleIsCentralized:
    """The rule is defined in one file and reaches SKILL.md through one pointer.

    SKILL.md used to restate the rule at each posting site (commit credit, reply
    bodies, follow-up issue snippet), repeating the same rationale three times.
    Centralizing removes that duplication and introduces a new failure mode in its
    place: the guardrail now reaches the agent through a *single* line, so deleting
    that line silently deletes the whole rule — with no template left behind to
    catch it. These tests pin the pointer.

    The pointer must be imperative. `skills/CLAUDE.md`: "Agents treat passive
    cross-references as informational and will skip them" — a rule stated once, in
    another file, behind a "see also", is a rule that does not fire.
    """

    SKILL_MD = SKILL_DIR / "SKILL.md"
    CANONICAL = SKILL_DIR / "references" / "commenter-ref.md"

    def _mandatory_pointers(self) -> list[str]:
        """Lines that *order* the agent to read the rule, not merely mention the file.

        A plain cross-reference is legal and useful — Step 2c's linkage dedup cites the
        file to explain why a bot reply carries no `@`. What must be unique is the
        mandatory pointer: the one line that makes the agent actually read the rule
        before posting.
        """
        return [
            line
            for line in self.SKILL_MD.read_text().splitlines()
            if "you must now execute" in line.lower() and "references/commenter-ref.md" in line
        ]

    def test_canonical_file_defines_the_rule(self):
        assert self.CANONICAL.exists(), f"{self.CANONICAL} is the rule's canonical home"
        text = self.CANONICAL.read_text()
        assert "{commenter_ref}" in text
        assert "Referring to the commenter" in text

    def test_skill_md_has_exactly_one_mandatory_pointer_to_the_rule(self):
        pointers = self._mandatory_pointers()
        assert len(pointers) == 1, (
            "SKILL.md must carry exactly one mandatory pointer to "
            "references/commenter-ref.md ('you must now execute'). Zero means the rule "
            "no longer reaches the agent at all — it is stated nowhere else, and no "
            "template is left behind to catch the omission. More than one means the "
            "duplication this refactor removed is creeping back. "
            f"Found {len(pointers)}:\n" + "\n".join(pointers)
        )

    def test_the_pointer_precedes_every_posting_step(self):
        """The pointer must sit ahead of Step 6d, Step 10, and Step 11 — the surfaces
        that post. A pointer placed at Step 10 would not cover Step 6d's nit replies.
        """
        lines = self.SKILL_MD.read_text().splitlines()
        pointer_at = next(
            i
            for i, line in enumerate(lines)
            if "you must now execute" in line.lower() and "references/commenter-ref.md" in line
        )
        first_posting_step = next(
            i for i, line in enumerate(lines) if line.startswith("### 6d.")
        )
        assert pointer_at < first_posting_step, (
            "The mandatory pointer must come before the first step that posts to GitHub "
            f"(Step 6d, line {first_posting_step + 1}); it is at line {pointer_at + 1}."
        )


class TestCommentFetchProjectionsCarryAuthorType:
    """The primary bot signal (`user.type == "Bot"`) is unusable unless it's fetched.

    is_bot_author's primary test is `author.get("type") == "Bot"` (reply-formats.md
    line ~27: "Do not test for a `[bot]` login suffix instead"). Each of the three
    comment-fetch jq projections in SKILL.md (Step 2 inline comments, Step 2b review
    bodies, Step 2c timeline comments) must therefore project `.user.type` alongside
    `.user.login`, or the agent only ever has a login string at runtime — and a bare
    `Copilot` (no `[bot]` suffix) is misclassified as human.
    """

    SKILL_MD = SKILL_DIR / "SKILL.md"

    def test_all_three_fetch_projections_carry_author_type(self):
        lines = self.SKILL_MD.read_text().splitlines()
        author_login_lines = [
            (lineno, line) for lineno, line in enumerate(lines, 1) if "author: .user.login" in line
        ]
        # Sanity check: if this drops to zero, the projections were removed or
        # renamed and this test would otherwise pass vacuously.
        assert len(author_login_lines) == 3, (
            "Expected exactly 3 comment-fetch jq projections with 'author: .user.login' "
            f"in SKILL.md (Steps 2/2b/2c); found {len(author_login_lines)}:\n"
            + "\n".join(f"{lineno}: {line.strip()}" for lineno, line in author_login_lines)
        )
        offenders = [
            f"{lineno}: {line.strip()}"
            for lineno, line in author_login_lines
            if "author_type: .user.type" not in line
        ]
        assert offenders == [], (
            "Comment-fetch jq projection drops '.user.type' — is_bot_author's primary "
            "signal is unfetchable, so a bare 'Copilot' login is misclassified as human:\n"
            + "\n".join(offenders)
        )


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
        nit = self._c("Copilot", "nit: rename `tmp` to `filtered`.", "2026-01-01T10:00:00Z")
        reply = self._c(
            "skillbot",
            "Copilot\n\nNoted as a nit — leaving as-is for now.",
            "2026-01-01T11:00:00Z",
        )
        assert is_already_addressed(nit, [nit, reply], pr_author="prowner", auth_user="skillbot") is False

    def test_human_reply_still_links_via_at_mention_alone(self):
        """The human path is unchanged: @mention alone suffices, no quote needed."""
        comment = self._c("alice", "Please add tests.", "2026-01-01T10:00:00Z")
        reply = self._c("skillbot", "@alice tests added, see latest commit.", "2026-01-01T11:00:00Z")
        assert is_already_addressed(comment, [comment, reply], pr_author="prowner", auth_user="skillbot") is True
