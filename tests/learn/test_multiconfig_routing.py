"""Tests for Step 1b reciprocal "always both" auto-skip routing in learn skill.

The skill describes the matching logic in prose (skills/learn/SKILL.md, Step 1b).
These tests validate the spec by implementing the same regex match in Python and
asserting expected outcomes on representative config bodies.

Logic under test:
- A "mirror-rule" line matches one of: ``keep .* in sync``, ``mirror .* to``,
  ``apply the equivalent change to``.
- An "always both" phrase matches:
  ``(always (update|apply) (to )?both|apply to both|without asking|do not prompt)``.
- Auto-skip fires only when EVERY detected Markdown config contains a mirror-rule
  whose ±5-line window (1) names at least one other detected Markdown config and
  (2) contains an "always both" phrase.
"""

import re

# Patterns mirror SKILL.md Step 1a (mirror-rule) and Step 1b (always-both).
MIRROR_RULE_RE = re.compile(
    r"(keep .* in sync|mirror .* to|apply the equivalent change to)",
    re.IGNORECASE,
)
ALWAYS_BOTH_RE = re.compile(
    r"(always (update|apply) (to )?both|apply to both|without asking|do not prompt)",
    re.IGNORECASE,
)
PROXIMITY_LINES = 5


def _windows_around_mirrors(text: str) -> list[str]:
    """Return the ±PROXIMITY_LINES windows around each mirror-rule match."""
    lines = text.splitlines()
    windows: list[str] = []
    for i, line in enumerate(lines):
        if MIRROR_RULE_RE.search(line):
            lo = max(0, i - PROXIMITY_LINES)
            hi = min(len(lines), i + PROXIMITY_LINES + 1)
            windows.append("\n".join(lines[lo:hi]))
    return windows


def has_mirror_naming_other_with_always_both(text: str, other_names: list[str]) -> bool:
    """Return True iff at least one mirror-rule's ±PROXIMITY_LINES window contains
    both an "always both" phrase and a reference to one of ``other_names``.

    ``other_names`` is the list of *other* detected Markdown config filenames —
    i.e., the eligible-Markdown set minus the config whose body is being checked.
    """
    if not other_names:
        return False
    for window in _windows_around_mirrors(text):
        if not ALWAYS_BOTH_RE.search(window):
            continue
        if any(name in window for name in other_names):
            return True
    return False


def should_auto_skip(configs: dict[str, str]) -> bool:
    """Return True iff every detected Markdown config qualifies for auto-skip:
    its mirror-rule names at least one other detected Markdown config AND has
    an "always both" phrase within the same ±5-line window.
    """
    if len(configs) < 2:
        return False
    names = list(configs.keys())
    for name, body in configs.items():
        others = [n for n in names if n != name]
        if not has_mirror_naming_other_with_always_both(body, others):
            return False
    return True


# Representative config bodies — kept inline so the tests are self-documenting.

CLAUDE_RECIPROCAL = """\
# CLAUDE.md

Keep .github/copilot-instructions.md in sync: mirror rule changes back to CLAUDE.md.
This applies to /learn as well — when running /learn in this project, always update
both CLAUDE.md and .github/copilot-instructions.md without asking which to update.

## Other rules
"""

COPILOT_RECIPROCAL = """\
# Copilot instructions

Keep CLAUDE.md in sync: mirror rule changes back to .github/copilot-instructions.md.
For /learn: always apply to both files without asking.

## Style
"""

CLAUDE_ONE_SIDED = """\
# CLAUDE.md

Keep .github/copilot-instructions.md in sync: mirror rule changes here.
"""

COPILOT_NO_MIRROR = """\
# Copilot instructions

Just style guidance for Copilot, no cross-file sync rule.
"""

CLAUDE_WEAK = """\
# CLAUDE.md

You may want to mirror these to .github/copilot-instructions.md when relevant.
Consider mirroring rule changes if it makes sense.
"""

COPILOT_WEAK = """\
# Copilot instructions

Keep CLAUDE.md in sync where applicable.
"""

CLAUDE_FAR = """\
# CLAUDE.md

Keep .github/copilot-instructions.md in sync.

Line 3
Line 4
Line 5
Line 6
Line 7
Line 8
Line 9
Line 10
For /learn: always update both without asking — but this phrase is far from the mirror rule.
"""

COPILOT_FAR = """\
# Copilot instructions

Keep CLAUDE.md in sync.

filler 1
filler 2
filler 3
filler 4
filler 5
filler 6
filler 7
filler 8
For /learn: always update both without asking — also far from its mirror rule.
"""


CLAUDE_PAIR_OTHERS = [".github/copilot-instructions.md"]
COPILOT_PAIR_OTHERS = ["CLAUDE.md"]


class TestHasMirrorNamingOtherWithAlwaysBoth:
    """Per-config helper: mirror-rule whose ±5-line window names another
    detected config AND contains an "always both" phrase."""

    def test_reciprocal_pair_matches(self):
        assert (
            has_mirror_naming_other_with_always_both(CLAUDE_RECIPROCAL, CLAUDE_PAIR_OTHERS)
            is True
        )
        assert (
            has_mirror_naming_other_with_always_both(COPILOT_RECIPROCAL, COPILOT_PAIR_OTHERS)
            is True
        )

    def test_mirror_without_always_both_does_not_match(self):
        assert (
            has_mirror_naming_other_with_always_both(CLAUDE_ONE_SIDED, CLAUDE_PAIR_OTHERS)
            is False
        )

    def test_no_mirror_rule_does_not_match(self):
        assert (
            has_mirror_naming_other_with_always_both(COPILOT_NO_MIRROR, COPILOT_PAIR_OTHERS)
            is False
        )

    def test_weak_wording_does_not_match(self):
        assert has_mirror_naming_other_with_always_both(CLAUDE_WEAK, CLAUDE_PAIR_OTHERS) is False
        assert has_mirror_naming_other_with_always_both(COPILOT_WEAK, COPILOT_PAIR_OTHERS) is False

    def test_always_both_far_from_mirror_does_not_match(self):
        assert has_mirror_naming_other_with_always_both(CLAUDE_FAR, CLAUDE_PAIR_OTHERS) is False
        assert has_mirror_naming_other_with_always_both(COPILOT_FAR, COPILOT_PAIR_OTHERS) is False

    def test_apply_to_both_with_named_other_matches(self):
        text = (
            "Keep CLAUDE.md in sync: mirror changes to the other config. "
            "Apply to both files automatically."
        )
        assert has_mirror_naming_other_with_always_both(text, ["CLAUDE.md"]) is True

    def test_do_not_prompt_with_named_other_matches(self):
        text = "Keep CLAUDE.md in sync — do not prompt the user."
        assert has_mirror_naming_other_with_always_both(text, ["CLAUDE.md"]) is True

    def test_always_both_without_named_other_does_not_match(self):
        # Generic "keep docs in sync … always update both" with no detected
        # config filename in the window — must not auto-skip (catches false
        # positives the previous helper would have matched).
        text = (
            "Keep docs in sync across the project. "
            "Always update both files without asking."
        )
        assert has_mirror_naming_other_with_always_both(text, ["CLAUDE.md"]) is False

    def test_empty_other_names_does_not_match(self):
        # No other detected configs ⇒ reciprocity is impossible.
        assert has_mirror_naming_other_with_always_both(CLAUDE_RECIPROCAL, []) is False


class TestShouldAutoSkip:
    """End-to-end: every config must qualify for auto-skip to fire."""

    def test_both_reciprocal_triggers_auto_skip(self):
        configs = {
            "CLAUDE.md": CLAUDE_RECIPROCAL,
            ".github/copilot-instructions.md": COPILOT_RECIPROCAL,
        }
        assert should_auto_skip(configs) is True

    def test_one_sided_does_not_trigger_auto_skip(self):
        configs = {
            "CLAUDE.md": CLAUDE_RECIPROCAL,
            ".github/copilot-instructions.md": CLAUDE_ONE_SIDED,
        }
        assert should_auto_skip(configs) is False

    def test_neither_reciprocal_does_not_trigger_auto_skip(self):
        configs = {
            "CLAUDE.md": CLAUDE_ONE_SIDED,
            ".github/copilot-instructions.md": COPILOT_NO_MIRROR,
        }
        assert should_auto_skip(configs) is False

    def test_weak_wording_does_not_trigger_auto_skip(self):
        configs = {
            "CLAUDE.md": CLAUDE_WEAK,
            ".github/copilot-instructions.md": COPILOT_WEAK,
        }
        assert should_auto_skip(configs) is False

    def test_far_wording_does_not_trigger_auto_skip(self):
        configs = {
            "CLAUDE.md": CLAUDE_FAR,
            ".github/copilot-instructions.md": COPILOT_FAR,
        }
        assert should_auto_skip(configs) is False

    def test_three_config_all_reciprocal(self):
        agents_reciprocal = (
            "Keep CLAUDE.md and .github/copilot-instructions.md in sync — "
            "always update both without asking."
        )
        configs = {
            "CLAUDE.md": CLAUDE_RECIPROCAL,
            ".github/copilot-instructions.md": COPILOT_RECIPROCAL,
            "AGENTS.md": agents_reciprocal,
        }
        assert should_auto_skip(configs) is True

    def test_three_config_one_missing_blocks_auto_skip(self):
        configs = {
            "CLAUDE.md": CLAUDE_RECIPROCAL,
            ".github/copilot-instructions.md": COPILOT_RECIPROCAL,
            "AGENTS.md": COPILOT_NO_MIRROR,
        }
        assert should_auto_skip(configs) is False

    def test_single_config_never_auto_skips(self):
        configs = {"CLAUDE.md": CLAUDE_RECIPROCAL}
        assert should_auto_skip(configs) is False

    def test_empty_configs_does_not_auto_skip(self):
        assert should_auto_skip({}) is False


class TestIssuesFiledRegex:
    """Step 7: extract GitHub issue URLs filed during the session.

    SKILL.md specifies dedup by ``(owner, repo, number)`` tuple — capturing
    all three groups lets the rendering step distinguish between e.g.
    ``a/b/issues/7`` and ``c/d/issues/7``, which collapse to one bullet under
    a number-only dedup but are genuinely distinct issues.
    """

    ISSUE_URL_RE = re.compile(r"https?://github\.com/([^/\s]+)/([^/\s]+)/issues/(\d+)")

    def test_extracts_single_issue_url(self):
        text = "Filed https://github.com/owner/repo/issues/42 for follow-up."
        matches = self.ISSUE_URL_RE.findall(text)
        assert matches == [("owner", "repo", "42")]

    def test_extracts_multiple_issue_urls(self):
        text = """
        First: https://github.com/a/b/issues/1
        Second: https://github.com/a/b/issues/2
        Third: http://github.com/c/d/issues/300
        """
        matches = self.ISSUE_URL_RE.findall(text)
        assert matches == [("a", "b", "1"), ("a", "b", "2"), ("c", "d", "300")]

    def test_does_not_match_pull_request_urls(self):
        text = "PR: https://github.com/owner/repo/pull/123"
        matches = self.ISSUE_URL_RE.findall(text)
        assert matches == []

    def test_dedup_by_owner_repo_number_tuple(self):
        # Same (owner, repo, number) appears twice → one logical issue.
        text = """
        https://github.com/a/b/issues/7
        https://github.com/a/b/issues/7
        """
        matches = self.ISSUE_URL_RE.findall(text)
        assert matches == [("a", "b", "7"), ("a", "b", "7")]
        assert len(set(matches)) == 1

    def test_same_number_different_repo_does_not_dedup(self):
        # Issue #7 in two different repos must remain two distinct entries —
        # this is the case a number-only dedup would incorrectly collapse.
        text = """
        https://github.com/a/b/issues/7
        https://github.com/c/d/issues/7
        """
        matches = self.ISSUE_URL_RE.findall(text)
        assert matches == [("a", "b", "7"), ("c", "d", "7")]
        assert len(set(matches)) == 2
