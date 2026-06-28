"""
Tests for the nit tagging and nits-only gate logic (spec 47):
- Step 6: `is_nit(body, action)` tags cosmetic `fix` / `accept suggestion` rows.
- Step 6d: `should_present_nit_table(rows, all_flag, manual)` decides whether the
  nits-only halt fires (auto mode only, ≥1 actionable row, all actionable nits).
"""

from conftest import is_nit, should_present_nit_table


class TestIsNitExplicitMarkers:
    """Explicit leading markers tag a fix/accept row as a nit (Step 6)."""

    def test_nit_colon_marker(self):
        assert is_nit("nit: rename this variable", "fix") is True

    def test_nitpick_marker(self):
        assert is_nit("nitpick: extra blank line here", "fix") is True

    def test_paren_nit_marker(self):
        assert is_nit("(nit) prefer const over let", "fix") is True

    def test_minor_marker(self):
        assert is_nit("minor: tighten this sentence", "fix") is True

    def test_style_marker(self):
        assert is_nit("style: use single quotes", "accept suggestion") is True

    def test_typo_marker(self):
        assert is_nit("typo: 'recieve' -> 'receive'", "fix") is True

    def test_marker_is_case_insensitive(self):
        assert is_nit("NIT: capitalize the heading", "fix") is True

    def test_marker_must_be_leading(self):
        # A "nit:" buried mid-sentence is not a leading marker; it only tags as
        # a nit if the semantic fallback independently matches (it does not here).
        assert is_nit("This is a real bug, not a nit: handle null", "fix") is False


class TestIsNitSeverityLabels:
    """Bot low/trivial severity labels tag a row as a nit (Step 6)."""

    def test_severity_low(self):
        assert is_nit("Severity: low — consider renaming", "fix") is True

    def test_severity_trivial(self):
        assert is_nit("severity: trivial cosmetic change", "accept suggestion") is True

    def test_bracketed_low(self):
        assert is_nit("[low] tidy up the import block", "fix") is True

    def test_low_severity_phrase(self):
        assert is_nit("This is a low severity formatting issue", "fix") is True


class TestIsNitSemanticFallback:
    """Representative cosmetic descriptions tag a row via the semantic fallback."""

    def test_spelling(self):
        assert is_nit("Fix the spelling in this comment", "fix") is True

    def test_rename_for_readability(self):
        assert is_nit("Rename `tmp` to `temp` for readability", "fix") is True

    def test_formatting(self):
        assert is_nit("Inconsistent formatting on this line", "accept suggestion") is True

    def test_whitespace(self):
        assert is_nit("Trailing whitespace here", "fix") is True

    def test_import_ordering(self):
        assert is_nit("Fix the import ordering", "fix") is True

    def test_wording(self):
        assert is_nit("Tighten the wording of this doc sentence", "fix") is True

    def test_phrasing(self):
        assert is_nit("Reword the phrasing here", "fix") is True


class TestIsNitConservativeDefault:
    """When in doubt, NOT a nit — substantive changes fall through to normal flow."""

    def test_functional_change_is_not_nit(self):
        assert is_nit("This off-by-one will skip the last element", "fix") is False

    def test_null_check_is_not_nit(self):
        assert is_nit("Add a null check before dereferencing", "fix") is False

    def test_empty_body_is_not_nit(self):
        assert is_nit("", "fix") is False

    def test_security_concern_is_not_nit(self):
        assert is_nit("This is vulnerable to SQL injection", "accept suggestion") is False


class TestIsNitActionGating:
    """The tag applies only to `fix` / `accept suggestion` (Step 6)."""

    def test_reply_is_never_nit(self):
        # Even with a marker, a reply row is never a nit.
        assert is_nit("nit: clarify this", "reply") is False

    def test_decline_is_never_nit(self):
        assert is_nit("style: use tabs", "decline") is False

    def test_skip_is_never_nit(self):
        assert is_nit("typo: fixme", "skip") is False

    def test_consistency_is_never_nit(self):
        assert is_nit("nit: rename for consistency", "consistency") is False


class TestStep5CarveOut:
    """Step 5 carve-out: an oversized comment, or any comment Step 5 flagged for
    manual review, is **never** a nit — even if its body reads as cosmetic
    (SKILL.md Step 6). `is_nit` is body-only and cannot enforce this; the
    carve-out excludes such rows upstream before tagging (see the `is_nit`
    docstring). These tests pin the contract so the carve-out is not silently
    lost: tagging an oversized cosmetic row `nit` would divert it to the
    lightweight nit table and drop Step 5's "manual review recommended" caveat.
    """

    def test_is_nit_is_body_only_and_cannot_enforce_the_carve_out(self):
        # A cosmetic body tags True on its own merits — nothing in is_nit knows
        # the comment was oversized or Step-5-flagged. Enforcement MUST happen
        # upstream, which is why such a row must reach tagging already nit=False.
        assert is_nit("typo: fix the heading spelling", "fix") is True

    def test_carved_out_row_modeled_as_non_nit_disqualifies_gate(self):
        # When Step 5 correctly carves out an oversized/flagged cosmetic comment,
        # the row arrives as an actionable fix with nit=False — which disqualifies
        # the Step 6d gate, routing to Step 7 where Step 5's caveat is preserved.
        rows = [{"action": "fix", "nit": False}]
        assert should_present_nit_table(rows) is False


class TestShouldPresentNitTable:
    """Step 6d gate trigger: auto mode, ≥1 actionable row, all actionable nits."""

    def test_all_nits_fires(self):
        rows = [
            {"action": "fix", "nit": True},
            {"action": "accept suggestion", "nit": True},
        ]
        assert should_present_nit_table(rows) is True

    def test_single_nit_fires(self):
        assert should_present_nit_table([{"action": "fix", "nit": True}]) is True

    def test_one_non_nit_fix_disqualifies(self):
        rows = [
            {"action": "fix", "nit": True},
            {"action": "fix", "nit": False},
        ]
        assert should_present_nit_table(rows) is False

    def test_reply_row_disqualifies(self):
        # A reply is actionable but never a nit → gate does not fire.
        rows = [
            {"action": "fix", "nit": True},
            {"action": "reply"},
        ]
        assert should_present_nit_table(rows) is False

    def test_decline_row_disqualifies(self):
        rows = [
            {"action": "accept suggestion", "nit": True},
            {"action": "decline"},
        ]
        assert should_present_nit_table(rows) is False

    def test_consistency_row_disqualifies(self):
        rows = [
            {"action": "fix", "nit": True},
            {"action": "consistency"},
        ]
        assert should_present_nit_table(rows) is False

    def test_skip_rows_are_ignored(self):
        # skip is non-actionable; an all-nit plan padded with skips still fires.
        rows = [
            {"action": "fix", "nit": True},
            {"action": "skip"},
        ]
        assert should_present_nit_table(rows) is True

    def test_empty_plan_does_not_fire(self):
        assert should_present_nit_table([]) is False

    def test_all_skip_does_not_fire(self):
        # All-skip belongs to Step 6c, not Step 6d.
        rows = [{"action": "skip"}, {"action": "skip"}]
        assert should_present_nit_table(rows) is False

    def test_all_flag_disables_gate(self):
        rows = [{"action": "fix", "nit": True}]
        assert should_present_nit_table(rows, all_flag=True) is False

    def test_manual_disables_gate(self):
        rows = [{"action": "fix", "nit": True}]
        assert should_present_nit_table(rows, manual=True) is False

    def test_all_flag_wins_even_with_manual_false(self):
        rows = [{"action": "fix", "nit": True}]
        assert should_present_nit_table(rows, all_flag=True, manual=False) is False
