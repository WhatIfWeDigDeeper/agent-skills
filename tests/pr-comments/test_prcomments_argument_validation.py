"""Argument validation tests for pr-comments (spec 39).

Verifies the SKILL.md Step 1 / Arguments section requirements:

- Any explicitly-supplied PR number must match ``^[1-9][0-9]{0,5}$`` (after
  stripping a single optional leading ``#`` and surrounding whitespace) before
  any shell call.
- Any ``--max N`` (and backward-compatible ``--auto N``) value must match
  ``^[1-9][0-9]{0,3}$`` before any shell call.

Both validators are exercised against the shared adversarial fixture list at
``tests/_helpers/argument_injection.py`` (landed in spec 36). The validators
themselves live in ``tests/pr-comments/conftest.py`` (``validate_pr_number`` /
``validate_max_value``) so the rest of the suite — ``is_pr_number`` /
``parse_pr_argument`` / ``parse_auto_flag`` — models the same spec-39 regexes
and cannot drift back to the looser ``isdigit()`` behavior.
"""

import sys
from pathlib import Path

import pytest

from conftest import parse_auto_flag, validate_max_value, validate_pr_number

sys.path.insert(0, str(Path(__file__).parent.parent / "_helpers"))
from argument_injection import ADVERSARIAL_ARGS


class TestValidPRNumbers:
    @pytest.mark.parametrize("value", ["1", "42", "123", "999", "10000", "999999"])
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


class TestPRNumberBoundaryRejections:
    @pytest.mark.parametrize(
        "value",
        [
            "0",            # zero is not a valid PR number
            "01",           # leading zero
            "1000000",      # 7 digits — exceeds the 6-digit cap
            "99999999999",  # ridiculous overflow
            "##42",         # double hash — only one leading # is stripped
        ],
    )
    def test_boundary_values_rejected(self, value: str) -> None:
        assert validate_pr_number(value) is False


class TestValidMaxValues:
    @pytest.mark.parametrize("value", ["1", "5", "10", "100", "9999"])
    def test_valid_values_accepted(self, value: str) -> None:
        assert validate_max_value(value) is True

    @pytest.mark.parametrize("value", ["  10", "10  ", "  100  "])
    def test_surrounding_whitespace_stripped(self, value: str) -> None:
        assert validate_max_value(value) is True


class TestAdversarialMaxValues:
    @pytest.mark.parametrize("value", ADVERSARIAL_ARGS)
    def test_adversarial_values_rejected(self, value: str) -> None:
        assert validate_max_value(value) is False


class TestMaxValueBoundaryRejections:
    @pytest.mark.parametrize(
        "value",
        [
            "0",        # zero is not a positive integer
            "01",       # leading zero
            "10000",    # 5 digits — exceeds the 4-digit cap
            "+10",      # signs are not part of the regex
            "#10",      # hash prefix is for PR numbers, not --max
        ],
    )
    def test_boundary_values_rejected(self, value: str) -> None:
        assert validate_max_value(value) is False


class TestParseAutoFlagMaxHandling:
    """parse_auto_flag must mirror the SKILL.md cap-value rules, not just consume."""

    @pytest.mark.parametrize(
        "args",
        ["--max 0", "--max 01", "--max 10000", "--auto 0", "--auto 99999", "--auto 01"],
    )
    def test_invalid_max_rejected_in_auto_mode(self, args: str) -> None:
        with pytest.raises(ValueError, match=r"Invalid --max value:"):
            parse_auto_flag(args)

    @pytest.mark.parametrize(
        ("args", "expected"),
        [
            ("--max 1", 1),
            ("--max 5", 5),
            ("--max 9999", 9999),
            ("--auto 7", 7),
            ("--max 5 42", 5),
        ],
    )
    def test_valid_max_applied_in_auto_mode(self, args: str, expected: int) -> None:
        result = parse_auto_flag(args)
        assert result["auto"] is True
        assert result["max_iterations"] == expected

    @pytest.mark.parametrize(
        "args",
        [
            "--manual --max 0",      # invalid value, but ignored in manual mode → no error
            "--max 0 --manual",      # order does not matter
            "--manual --max 5",      # valid value, still ignored in manual mode
            "--max 5 --manual",
            "--auto 5 --manual",     # --manual wins; --auto 5 ignored
            "--manual --auto",       # --manual is sticky; trailing --auto is a no-op
            "--manual --auto 99999", # value would fail validation, but manual mode never raises
            "--auto 99999 --manual", # same, regardless of order
        ],
    )
    def test_max_ignored_in_manual_mode(self, args: str) -> None:
        result = parse_auto_flag(args)
        assert result["auto"] is False
        assert result["max_iterations"] == 10  # default; supplied value ignored

    @pytest.mark.parametrize("args", ["--manual --auto", "--auto --manual", "--manual --auto 5"])
    def test_manual_is_sticky_against_auto(self, args: str) -> None:
        """Once --manual appears, --auto never re-enables auto mode (any token order)."""
        assert parse_auto_flag(args)["auto"] is False

    def test_invalid_max_value_token_not_leaked_to_remaining_args(self) -> None:
        """A digit-like invalid value is consumed by --max (raises), never reaching remaining_args."""
        with pytest.raises(ValueError):
            parse_auto_flag("--max 0 42")
