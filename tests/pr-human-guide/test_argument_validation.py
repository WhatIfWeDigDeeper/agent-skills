"""PR number validation tests for pr-human-guide (spec 37).

Verifies the SKILL.md Step 1 requirement: any explicitly-supplied PR number
must match ^[1-9][0-9]{0,5}$ (after stripping a single optional leading '#')
before any shell call. Uses the shared adversarial fixture list from
tests/_helpers/argument_injection.py.
"""

import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "_helpers"))
from argument_injection import ADVERSARIAL_ARGS

PR_NUMBER_RE = re.compile(r"^[1-9][0-9]{0,5}\Z")


def validate_pr_number(value: str) -> bool:
    """Return True if value is a valid PR number per SKILL.md Step 1.

    Strips surrounding spaces/tabs, then a single leading '#' (so '42',
    '#42', and '  42  ' all accepted), then matches against PR_NUMBER_RE.

    Strip is limited to ASCII space and tab so newline / carriage-return
    smuggled at the boundary (e.g. "1\\n") is not silently normalized away
    before the regex check — the ``\\Z`` anchor must do the final reject.
    """
    cleaned = str(value).strip(" \t").removeprefix("#")
    return bool(PR_NUMBER_RE.match(cleaned))


class TestValidPRNumbers:
    @pytest.mark.parametrize("value", ["1", "42", "123", "999", "10000"])
    def test_valid_values_accepted(self, value: str) -> None:
        assert validate_pr_number(value) is True

    @pytest.mark.parametrize("value", ["#1", "#42", "#999"])
    def test_hash_prefix_accepted(self, value: str) -> None:
        assert validate_pr_number(value) is True

    @pytest.mark.parametrize("value", ["  42", "42  ", "  42  ", "  #42  "])
    def test_surrounding_whitespace_stripped(self, value: str) -> None:
        assert validate_pr_number(value) is True


class TestAdversarialPRNumbers:
    @pytest.mark.parametrize("value", ADVERSARIAL_ARGS)
    def test_adversarial_values_rejected(self, value: str) -> None:
        assert validate_pr_number(value) is False
