"""
Tests for the regression-test-with-every-substantive-code-fix gate (spec 51):
- Step 8: `requires_regression_test(action, body, touches_code)` decides whether
  a planned row must carry a regression test in the same commit as its fix
  (test-first / TDD). True only for non-nit `fix` / `accept suggestion` rows
  whose edit touches executable code; False for nits, non-code changes, and
  `reply` / `decline` / `skip` / `consistency`.
"""

from conftest import requires_regression_test


class TestRequiredForSubstantiveCodeFixes:
    """Non-nit code-editing rows touching code require a regression test."""

    def test_plain_fix_touching_code(self):
        assert (
            requires_regression_test("fix", "Guard against a null user before deref", True)
            is True
        )

    def test_accept_suggestion_touching_code(self):
        assert (
            requires_regression_test(
                "accept suggestion", "Off-by-one in the loop bound", True
            )
            is True
        )

    def test_empty_body_still_requires_when_code_and_not_nit(self):
        # A missing body is not a nit signal; a code-touching fix still needs a guard.
        assert requires_regression_test("fix", "", True) is True


class TestNitsAreExempt:
    """Rows tagged a nit in Step 6 never require a regression test."""

    def test_nit_marker_fix(self):
        assert (
            requires_regression_test("fix", "nit: rename this variable", True) is False
        )

    def test_nit_marker_accept_suggestion(self):
        assert (
            requires_regression_test(
                "accept suggestion", "style: use single quotes", True
            )
            is False
        )

    def test_semantic_nit_typo(self):
        assert requires_regression_test("fix", "fix a typo in the comment", True) is False

    def test_low_severity_label(self):
        assert requires_regression_test("fix", "[low] tidy the imports", True) is False


class TestNonCodeChangesAreExempt:
    """A fix that touches no executable code has no runtime surface to guard."""

    def test_docs_only_fix(self):
        assert (
            requires_regression_test("fix", "Clarify the setup instructions", False)
            is False
        )

    def test_accept_suggestion_non_code(self):
        assert (
            requires_regression_test(
                "accept suggestion", "Reword this error message copy", False
            )
            is False
        )


class TestNonCodeEditingActionsAreExempt:
    """reply / decline / skip / consistency never edit the author's code here."""

    def test_reply(self):
        assert requires_regression_test("reply", "Answering the reviewer question", True) is False

    def test_decline(self):
        assert requires_regression_test("decline", "Out of scope for this PR", True) is False

    def test_skip(self):
        assert requires_regression_test("skip", "outdated thread", True) is False

    def test_consistency(self):
        # Consistency rows ride along with their originating fix; they are not
        # independently gated for a test.
        assert requires_regression_test("consistency", "Sync the sibling reference", True) is False


class TestBranchesAreDistinct:
    """Each guard clause is load-bearing — flipping one input flips the verdict."""

    def test_touches_code_is_load_bearing(self):
        assert requires_regression_test("fix", "Real behavioral fix", True) is True
        assert requires_regression_test("fix", "Real behavioral fix", False) is False

    def test_nit_is_load_bearing(self):
        assert requires_regression_test("fix", "Real behavioral fix", True) is True
        assert requires_regression_test("fix", "nit: cosmetic tweak", True) is False

    def test_action_is_load_bearing(self):
        assert requires_regression_test("fix", "Real behavioral fix", True) is True
        assert requires_regression_test("reply", "Real behavioral fix", True) is False
