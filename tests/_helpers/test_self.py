"""Sanity tests for tests/_helpers/argument_injection.py.

Confirms the helper module imports and that its constants carry the
expected attack vectors so downstream skill test suites can rely on them.
"""

from argument_injection import (
    ADVERSARIAL_ARGS,
    ADVERSARIAL_TEXT_ARGS,
)


def test_adversarial_args_non_empty():
    assert len(ADVERSARIAL_ARGS) > 10


def test_adversarial_text_args_non_empty():
    assert len(ADVERSARIAL_TEXT_ARGS) > 5


def test_shell_metacharacter_coverage():
    joined = "\n".join(ADVERSARIAL_ARGS)
    assert ";" in joined
    assert "&&" in joined
    assert "$(" in joined
    assert "`" in joined
    assert "|" in joined


def test_text_args_metacharacter_coverage():
    joined = "\n".join(ADVERSARIAL_TEXT_ARGS)
    assert ";" in joined
    assert "$(" in joined
    assert "`" in joined


def test_unicode_homoglyph_coverage():
    joined = "".join(ADVERSARIAL_ARGS) + "".join(ADVERSARIAL_TEXT_ARGS)
    # Fullwidth digit one, zero-width space, en-dash, RTL override.
    # Use \uXXXX escapes here for the same readability reason as in
    # argument_injection.py — raw glyphs render invisibly in most editors.
    assert "\uFF11" in joined
    assert "\u200B" in joined
    assert "\u2013" in joined
    assert "\u202E" in joined
