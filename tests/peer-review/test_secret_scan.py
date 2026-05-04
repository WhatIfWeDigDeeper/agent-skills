"""Tests for SKILL.md Step 4b — pre-flight secret scan and confirmation routing.

The Step 4b dispatch (which patterns fire on which inputs) and the y/abort
confirmation branch are classifiable workflow logic per CLAUDE.md, so they
get unit coverage alongside argument parsing and model routing.
"""

import pytest

from conftest import (
    route_confirmation_response,
    secret_scan,
    should_run_secret_scan,
)


# --- Routing: scan only fires on the external CLI path ---


@pytest.mark.parametrize(
    "model",
    [
        None,
        "self",
        "Self",
        "claude-opus-4-5",
        "claude-sonnet-4-6",
    ],
)
def test_secret_scan_skipped_on_internal_route(model):
    """Self / claude-* keep content inside the runtime — no pre-flight scan."""
    assert should_run_secret_scan(model) is False


@pytest.mark.parametrize(
    "model",
    [
        "copilot",
        "copilot:gpt-5",
        "codex",
        "codex:o4",
        "gemini",
        "gemini:gemini-2.0-flash",
    ],
)
def test_secret_scan_required_on_external_route(model):
    """Copilot / codex / gemini send the prompt to a third-party CLI — scan first."""
    assert should_run_secret_scan(model) is True


# --- Pattern matching: positive cases (each pattern fires on a realistic example) ---


def test_pem_private_key_matches():
    prompt = "-----BEGIN RSA PRIVATE KEY-----\nMIIEowIBAAKCAQEA...\n-----END RSA PRIVATE KEY-----"  # cspell:disable-line
    hits = secret_scan(prompt)
    names = [name for name, _ in hits]
    assert "PEM private key" in names


def test_pem_openssh_private_key_matches():
    """The `[A-Z ]+` allows multi-word headers like `OPENSSH PRIVATE KEY`."""
    prompt = "-----BEGIN OPENSSH PRIVATE KEY-----\nb3BlbnNzaC1rZXkt...\n"  # cspell:disable-line
    hits = secret_scan(prompt)
    assert any(name == "PEM private key" for name, _ in hits)


def test_github_pat_ghp_matches():
    # Build the token at runtime so the source file does not contain a
    # contiguous `ghp_<36 chars>` literal — many secret scanners and GitHub
    # push-protection hooks fire on the raw text shape alone, even for
    # obvious test fixtures. The runtime string is identical, so the regex
    # under test still sees the same input.
    prompt = "token = " + "ghp_" + "AbCdEfGhIjKlMnOpQrStUvWxYzAbCdEfGhIj"
    hits = secret_scan(prompt)
    names = [name for name, _ in hits]
    assert "GitHub PAT (ghp_)" in names


@pytest.mark.parametrize(
    "prefix,expected_name",
    [
        ("gho_", "GitHub OAuth (gho_)"),
        ("ghs_", "GitHub server (ghs_)"),
        ("ghu_", "GitHub user (ghu_)"),
    ],
)
def test_github_other_token_prefixes_match(prefix, expected_name):
    prompt = f"token = {prefix}AbCdEfGhIjKlMnOpQrStUvWxYzAbCdEfGhIj"
    hits = secret_scan(prompt)
    names = [name for name, _ in hits]
    assert expected_name in names


def test_openai_sk_key_matches():
    prompt = "OPENAI_API_KEY=sk-AbCdEfGhIjKlMnOpQrStUvWx"
    hits = secret_scan(prompt)
    names = [name for name, _ in hits]
    assert "OpenAI/Anthropic-style (sk-)" in names


def test_anthropic_sk_ant_api03_matches():
    """The widened `[A-Za-z0-9_-]{20,}` inner class lets `sk-ant-api03-...`
    match across its internal hyphens — round-6 fix per Copilot 3175565548."""
    prompt = "ANTHROPIC_API_KEY=sk-ant-api03-AbCdEfGhIjKlMnOpQrStUvWx_yz"
    hits = secret_scan(prompt)
    matches = [m for name, m in hits if name == "OpenAI/Anthropic-style (sk-)"]
    assert matches, "sk-ant-api03- shape should match"
    # Match should include the full key shape, not stop at the first hyphen
    assert "ant-api03" in matches[0]


def test_openai_sk_proj_matches():
    """`sk-proj-...` shape similarly spans hyphens in the body."""
    prompt = "OPENAI_KEY=sk-proj-AbCdEfGhIjKlMnOpQrStUvWxYz"
    hits = secret_scan(prompt)
    matches = [m for name, m in hits if name == "OpenAI/Anthropic-style (sk-)"]
    assert matches
    assert "proj" in matches[0]


@pytest.mark.parametrize(
    "innocent",
    [
        "risk-mitigation-recommendations-list-for-the-quarter",
        "task-management-and-planning-discussion-thread",
        "disk-encryption-rollout-status-update-and-notes",
        "asksomething-or-other-but-not-a-key-just-words",  # cspell:disable-line
    ],
)
def test_sk_boundary_anchor_skips_innocent_substrings(innocent):
    """The `(^|[^A-Za-z0-9])` boundary anchor avoids matching `risk-…`/`task-…`/
    `disk-…` and similar English compounds — round-6 boundary-anchor fix."""
    hits = secret_scan(innocent)
    sk_hits = [name for name, _ in hits if name == "OpenAI/Anthropic-style (sk-)"]
    assert sk_hits == [], f"boundary anchor should reject {innocent!r}"


def test_sk_at_line_start_matches():
    """A real key at the very start of the prompt (no preceding character) must still
    match — the `^` alternation in `(^|[^A-Za-z0-9])` handles this case."""
    prompt = "sk-AbCdEfGhIjKlMnOpQrStUvWx"
    hits = secret_scan(prompt)
    assert any(name == "OpenAI/Anthropic-style (sk-)" for name, _ in hits)


def test_aws_access_key_matches():
    prompt = "AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE"  # cspell:disable-line
    hits = secret_scan(prompt)
    names = [name for name, _ in hits]
    assert "AWS access key (AKIA)" in names


def test_aws_lowercase_akia_does_not_match():
    """AWS keys are strictly uppercase — `akia…` is an English word, not a key.
    The SKILL.md Step 4b note "Do not collapse both groups into a single
    `grep -Ei` call" explicitly warns against case-folding `[0-9A-Z]` to
    `[0-9A-Za-z]` because it would falsely match `akiamatashotokugawamotoharu`."""
    prompt = "consider akiamatashotokugawamotoharu as a counterexample"
    hits = secret_scan(prompt)
    aws_hits = [name for name, _ in hits if name == "AWS access key (AKIA)"]
    assert aws_hits == []


@pytest.mark.parametrize("prefix", ["xoxb", "xoxa", "xoxp", "xoxr", "xoxs"])
def test_slack_token_matches(prefix):
    prompt = f"SLACK_TOKEN={prefix}-1234567890-abcdefghij"
    hits = secret_scan(prompt)
    names = [name for name, _ in hits]
    assert "Slack token (xox*)" in names


@pytest.mark.parametrize(
    "line",
    [
        "api_key = AbCdEfGhIjKlMnOp",
        "API-KEY: AbCdEfGhIjKlMnOp",
        "secret=AbCdEfGhIjKlMnOpQrStUvWx",
        "PASSWORD = 'AbCdEfGhIjKlMnOpQr'",
        "bearer: AbCdEfGhIjKlMnOpQrStUv",
        "Authorization: AbCdEfGhIjKlMnOpQrStUv",
    ],
)
def test_generic_credential_assignment_matches(line):
    """The case-insensitive group catches generic `keyword: value` shapes."""
    hits = secret_scan(line)
    names = [name for name, _ in hits]
    assert "Generic credential assignment" in names


@pytest.mark.parametrize(
    "split",
    [
        "api_key:\nAbCdEfGhIjKlMnOpQrStUv",
        "secret =\nAbCdEfGhIjKlMnOpQrStUvWxYz",
        "Authorization:\r\nAbCdEfGhIjKlMnOpQrStUv",
        "password=\n\nAbCdEfGhIjKlMnOpQrStUvWx",
    ],
)
def test_generic_credential_assignment_does_not_span_lines(split):
    """`grep -Ei` is line-based — the keyword on one line and the value on the
    next must not match. Two layers keep this faithful: the pattern uses
    `[ \\t]*` (ASCII spaces/tabs only, no `\\n`) instead of Python's
    Unicode-aware `\\s*`, and `secret_scan()` additionally iterates over
    `splitlines()` so any future `\\s` pattern stays line-bounded too."""
    hits = secret_scan(split)
    names = [name for name, _ in hits]
    assert "Generic credential assignment" not in names


# --- Pattern matching: negative cases (clean prompts must produce no matches) ---


@pytest.mark.parametrize(
    "clean",
    [
        "diff --git a/foo.py b/foo.py\n+def hello(): return 'world'",
        "Refactor the parser to handle nested arrays correctly.",
        "Updated README with new install instructions.",
        "",
        "fix: typo in error message",
        "see commit ghp_short for context",  # too short for ghp_ pattern
        "sk-tooshort",  # cspell:disable-line — under 20 chars after `sk-`
    ],
)
def test_clean_prompt_produces_no_matches(clean):
    assert secret_scan(clean) == []


def test_multiple_distinct_secrets_all_reported():
    """When several patterns fire, all of their names appear in the result."""
    # Same runtime-concatenation trick as `test_github_pat_ghp_matches` —
    # keeps the source file free of contiguous `ghp_<36 chars>` literals so
    # secret scanners and push-protection hooks do not fire on this fixture.
    prompt = (
        "github = " + "ghp_" + "AbCdEfGhIjKlMnOpQrStUvWxYzAbCdEfGhIj\n"
        "openai = sk-AbCdEfGhIjKlMnOpQrStUvWx\n"
        "aws = AKIAIOSFODNN7EXAMPLE\n"  # cspell:disable-line
    )
    hits = secret_scan(prompt)
    names = {name for name, _ in hits}
    assert "GitHub PAT (ghp_)" in names
    assert "OpenAI/Anthropic-style (sk-)" in names
    assert "AWS access key (AKIA)" in names


# --- Confirmation routing: y → proceed, anything else → abort ---


@pytest.mark.parametrize("response", ["y", "Y", " y ", "y\n"])
def test_confirmation_y_proceeds(response):
    assert route_confirmation_response(response) == "proceed"


@pytest.mark.parametrize(
    "response",
    [
        "n",
        "N",
        "no",
        "yes",  # strict — only `y` proceeds, not `yes`
        "yep",
        "maybe",
        "",
        "   ",
        "\n",
        None,
    ],
)
def test_confirmation_anything_else_aborts(response):
    """Per the SKILL.md Step 4b confirmation-routing rule "anything else
    (including empty input) → exit" — strict match on `y`; `yes`, blank input,
    and None all route to abort."""
    assert route_confirmation_response(response) == "abort"
