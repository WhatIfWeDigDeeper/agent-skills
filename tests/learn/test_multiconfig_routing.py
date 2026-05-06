"""Tests for Step 1b reciprocal "always both" auto-skip routing in learn skill.

The skill describes the matching logic in prose (skills/learn/SKILL.md, Step 1b).
These tests validate the spec by implementing the same regex match in Python and
asserting expected outcomes on representative config bodies.

Logic under test:
- A "mirror-rule" line matches one of: ``keep .* in sync``, ``mirror .* to``,
  ``apply the equivalent change``.
- An "always both" phrase matches:
  ``(always (update|apply) (to )?both|apply to both|without asking|do not prompt)``.
- Auto-skip fires only when EVERY detected config contains a mirror-rule AND an
  "always both" phrase within 5 lines of that mirror-rule.
"""

import re

# Patterns mirror SKILL.md Step 1a (mirror-rule) and Step 1b (always-both).
MIRROR_RULE_RE = re.compile(
    r"(keep .* in sync|mirror .* to|apply the equivalent change)",
    re.IGNORECASE,
)
ALWAYS_BOTH_RE = re.compile(
    r"(always (update|apply) (to )?both|apply to both|without asking|do not prompt)",
    re.IGNORECASE,
)
PROXIMITY_LINES = 5


def has_mirror_with_always_both(text: str) -> bool:
    """Return True iff at least one mirror-rule has an "always both" phrase
    within ``PROXIMITY_LINES`` lines (in either direction)."""
    lines = text.splitlines()
    mirror_indices = [i for i, line in enumerate(lines) if MIRROR_RULE_RE.search(line)]
    for idx in mirror_indices:
        lo = max(0, idx - PROXIMITY_LINES)
        hi = min(len(lines), idx + PROXIMITY_LINES + 1)
        window = "\n".join(lines[lo:hi])
        if ALWAYS_BOTH_RE.search(window):
            return True
    return False


def should_auto_skip(configs: dict[str, str]) -> bool:
    """Return True iff every config qualifies for the reciprocal auto-skip."""
    if len(configs) < 2:
        return False
    return all(has_mirror_with_always_both(body) for body in configs.values())


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


class TestHasMirrorWithAlwaysBoth:
    """Per-config helper: mirror-rule + 'always both' within proximity."""

    def test_reciprocal_pair_matches(self):
        assert has_mirror_with_always_both(CLAUDE_RECIPROCAL) is True
        assert has_mirror_with_always_both(COPILOT_RECIPROCAL) is True

    def test_mirror_without_always_both_does_not_match(self):
        assert has_mirror_with_always_both(CLAUDE_ONE_SIDED) is False

    def test_no_mirror_rule_does_not_match(self):
        assert has_mirror_with_always_both(COPILOT_NO_MIRROR) is False

    def test_weak_wording_does_not_match(self):
        assert has_mirror_with_always_both(CLAUDE_WEAK) is False
        assert has_mirror_with_always_both(COPILOT_WEAK) is False

    def test_always_both_far_from_mirror_does_not_match(self):
        assert has_mirror_with_always_both(CLAUDE_FAR) is False
        assert has_mirror_with_always_both(COPILOT_FAR) is False

    def test_apply_to_both_phrase_matches(self):
        text = "Mirror changes to the other config. Apply to both files automatically."
        assert has_mirror_with_always_both(text) is True

    def test_do_not_prompt_phrase_matches(self):
        text = "Keep both configs in sync — do not prompt the user."
        assert has_mirror_with_always_both(text) is True


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
    """Step 7: extract GitHub issue URLs filed during the session."""

    ISSUE_URL_RE = re.compile(r"https?://github\.com/[^/\s]+/[^/\s]+/issues/(\d+)")

    def test_extracts_single_issue_url(self):
        text = "Filed https://github.com/owner/repo/issues/42 for follow-up."
        matches = self.ISSUE_URL_RE.findall(text)
        assert matches == ["42"]

    def test_extracts_multiple_issue_urls(self):
        text = """
        First: https://github.com/a/b/issues/1
        Second: https://github.com/a/b/issues/2
        Third: http://github.com/c/d/issues/300
        """
        matches = self.ISSUE_URL_RE.findall(text)
        assert matches == ["1", "2", "300"]

    def test_does_not_match_pull_request_urls(self):
        text = "PR: https://github.com/owner/repo/pull/123"
        matches = self.ISSUE_URL_RE.findall(text)
        assert matches == []

    def test_dedup_by_issue_number(self):
        text = """
        https://github.com/a/b/issues/7
        https://github.com/a/b/issues/7
        """
        matches = self.ISSUE_URL_RE.findall(text)
        # Regex finds each occurrence; dedup happens at render time per SKILL.md.
        assert matches == ["7", "7"]
        assert len(set(matches)) == 1
