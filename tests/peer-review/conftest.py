"""Pytest fixtures and helpers for peer-review skill tests."""

import re

HELP_TRIGGERS = {"help", "--help", "-h", "?"}

_PR_RE = re.compile(r'^[1-9][0-9]*$')
_BRANCH_RE = re.compile(r'^[A-Za-z0-9._/-]+$')


def is_help_request(args: str | None) -> bool:
    """Check if arguments are a help request per SKILL.md."""
    return args.strip().lower() in HELP_TRIGGERS if args and args.strip() else False


def parse_arguments(args: str | list[str] | None) -> dict:
    """Parse peer-review arguments per SKILL.md.

    Accepts either a raw string (which is then tokenized via str.split — same
    as the runtime path) or a pre-tokenized list[str] (used by tests that need
    to exercise validation branches unreachable via str.split, such as an
    empty/whitespace-only `--focus` topic).

    Returns:
        {
            "target_type": "staged" | "pr" | "branch" | "path" | None,
            "pr_number": str | None,
            "branch_name": str | None,
            "path": str | None,
            "model": str | None,  # Defaults to "self" on successful parses; on error, it may be None or a previously parsed value.
            "focus": str | None,
            "explicit_staged": bool,
            "error": str | None,
        }

    Interpretation invariant:
        - target_type == "staged" and explicit_staged == True means the caller
          explicitly passed --staged.
        - target_type == "staged" and explicit_staged == False means no
          explicit target was supplied, so the default staged/auto-detect
          behavior applies.
        - In particular, no args returns target_type == "staged" with
          explicit_staged == False; callers must not treat that as an
          explicit staged-only request.
    """
    result = {
        "target_type": None,
        "pr_number": None,
        "branch_name": None,
        "path": None,
        "model": None,
        "focus": None,
        "explicit_staged": False,
        "error": None,
    }

    if isinstance(args, list):
        tokens = args
        if not tokens:
            result["target_type"] = "staged"
            result["model"] = "self"
            return result
    else:
        if not args or not args.strip():
            result["target_type"] = "staged"
            result["model"] = "self"
            return result
        tokens = args.strip().split()
    i = 0
    target_count = 0

    while i < len(tokens):
        tok = tokens[i]

        if tok == "--staged":
            target_count += 1
            if target_count > 1:
                result["error"] = "specify one target at a time — targets are mutually exclusive."
                return result
            result["target_type"] = "staged"
            result["explicit_staged"] = True
            i += 1

        elif tok == "--pr":
            target_count += 1
            if target_count > 1:
                result["error"] = "specify one target at a time — targets are mutually exclusive."
                return result
            if i + 1 >= len(tokens):
                result["error"] = "--pr requires a PR number"
                return result
            result["target_type"] = "pr"
            result["pr_number"] = tokens[i + 1]
            if not _PR_RE.match(result["pr_number"]):
                result["error"] = f"--pr requires a positive integer, got: {result['pr_number']}"
                return result
            i += 2

        elif tok == "--branch":
            target_count += 1
            if target_count > 1:
                result["error"] = "specify one target at a time — targets are mutually exclusive."
                return result
            if i + 1 >= len(tokens):
                result["error"] = "--branch requires a branch name"
                return result
            result["target_type"] = "branch"
            result["branch_name"] = tokens[i + 1]
            if not _BRANCH_RE.match(result["branch_name"]):
                result["error"] = f"--branch requires a git ref name (letters, digits, ., _, /, -), got: {result['branch_name']}"
                return result
            i += 2

        elif tok == "--model":
            if i + 1 >= len(tokens):
                result["error"] = "--model requires a model name"
                return result
            result["model"] = tokens[i + 1]
            i += 2

        elif tok == "--focus":
            if i + 1 >= len(tokens):
                result["error"] = "--focus requires a non-empty topic"
                return result
            topic = tokens[i + 1]
            if not topic.strip():
                result["error"] = "--focus requires a non-empty topic"
                return result
            result["focus"] = topic
            i += 2

        else:
            # Remaining token treated as path
            target_count += 1
            if target_count > 1:
                result["error"] = "specify one target at a time — targets are mutually exclusive."
                return result
            result["target_type"] = "path"
            result["path"] = tok
            i += 1

    if result["target_type"] is None:
        result["target_type"] = "staged"

    if result["model"] is None:
        result["model"] = "self"

    return result


def detect_mode(has_plan_md: bool, has_tasks_md: bool) -> str:
    """Detect review mode from directory contents per SKILL.md.

    Returns: "consistency" (spec mode was removed in v1.3; plan.md+tasks.md
    directories now use consistency mode like any other path target)
    """
    return "consistency"


def route_model(model: str | None) -> dict:
    """Determine reviewer route from --model value per SKILL.md Step 4.

    Returns:
        {
            "route": "internal" | "copilot" | "codex" | "gemini",
            "binary": str | None,  # CLI binary name (None for internal path)
            "submodel": str | None,  # Sub-model if specified after ':'
        }
    """
    if not model:
        return {"route": "internal", "binary": None, "submodel": None}

    model_lower = model.lower()
    if model_lower == "self" or model_lower.startswith("claude-"):
        return {"route": "internal", "binary": None, "submodel": None}

    if ":" in model:
        prefix, submodel = model.split(":", 1)
    else:
        prefix, submodel = model, None

    prefix_lower = prefix.lower()
    if prefix_lower == "copilot":
        return {"route": "copilot", "binary": "copilot", "submodel": submodel}
    elif prefix_lower == "codex":
        return {"route": "codex", "binary": "codex", "submodel": submodel}
    elif prefix_lower == "gemini":
        return {"route": "gemini", "binary": "gemini", "submodel": submodel}

    raise ValueError(
        f"Unsupported --model value: '{model}'. "
        "Supported values: self (default), claude-* (if your assistant supports model selection), "
        "copilot[:submodel], codex[:submodel], gemini[:submodel]."
    )


# Step 4b — Pre-flight secret scan (external CLI path only).
# Patterns mirror SKILL.md L317-325 — POSIX ERE in the spec, translated to
# Python regex here (Python uses `\s`/`\w` rather than POSIX bracket classes;
# semantics are equivalent for the spec's pattern set).
_SECRET_PATTERNS_CASE_SENSITIVE = [
    ("PEM private key", re.compile(r"-----BEGIN [A-Z ]+PRIVATE KEY-----")),
    ("GitHub PAT (ghp_)", re.compile(r"ghp_[A-Za-z0-9]{36,}")),
    ("GitHub OAuth (gho_)", re.compile(r"gho_[A-Za-z0-9]{36,}")),
    ("GitHub server (ghs_)", re.compile(r"ghs_[A-Za-z0-9]{36,}")),
    ("GitHub user (ghu_)", re.compile(r"ghu_[A-Za-z0-9]{36,}")),
    ("OpenAI/Anthropic-style (sk-)", re.compile(r"(^|[^A-Za-z0-9])sk-[A-Za-z0-9_-]{20,}")),
    ("AWS access key (AKIA)", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("Slack token (xox*)", re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}")),
]

_SECRET_PATTERNS_CASE_INSENSITIVE = [
    (
        "Generic credential assignment",
        re.compile(
            r"(api[_-]?key|secret|password|bearer|authorization)\s*[:=]\s*['\"]?[A-Za-z0-9+/_=-]{16,}",
            re.IGNORECASE,
        ),
    ),
]


def should_run_secret_scan(model: str | None) -> bool:
    """SKILL.md Step 4b runs the pre-flight secret scan only on the external CLI path.

    Internal routes (self / claude-*) keep content inside the assistant runtime and
    skip the scan; copilot/codex/gemini send the prompt to a third-party CLI and
    must run the scan first.
    """
    route = route_model(model)["route"]
    return route != "internal"


def secret_scan(prompt: str) -> list[tuple[str, str]]:
    """Run both grep -E groups from SKILL.md Step 4b against `prompt`.

    Returns a list of `(pattern_name, matched_substring)` tuples — empty when
    the prompt is clean. A match in either group counts; both groups are run
    independently per the spec's "two grep invocations" requirement.

    Scanning is line-by-line to mirror `grep -E` / `grep -Ei` semantics: in
    Python `re`, character classes like `\\s` match `\\n`/`\\r`, which would
    let a pattern like `secret\\s*=\\s*VALUE` span line breaks. `grep` is
    line-based and cannot, so the unit helper iterates over `splitlines()` to
    keep the documented behavior faithful. Each pattern is reported at most
    once per scan (first matching line wins) — same as a single
    `grep -E PATTERN` invocation.
    """
    matches: list[tuple[str, str]] = []
    lines = prompt.splitlines() or [prompt]
    for name, pat in _SECRET_PATTERNS_CASE_SENSITIVE:
        for line in lines:
            m = pat.search(line)
            if m:
                matches.append((name, m.group(0)))
                break
    for name, pat in _SECRET_PATTERNS_CASE_INSENSITIVE:
        for line in lines:
            m = pat.search(line)
            if m:
                matches.append((name, m.group(0)))
                break
    return matches


def route_confirmation_response(response: str | None) -> str:
    """SKILL.md Step 4b confirmation routing: `y` proceeds, anything else aborts.

    Returns "proceed" or "abort". Empty input, whitespace-only input, and any
    non-`y` reply all route to "abort" per the spec's "anything else (including
    empty input)" clause. The check is exact-match on `y` (case-insensitive,
    stripped) — `y`, `Y`, ` y `, `Y\n` proceed; `yes`, `yep`, `n`, `no`,
    `maybe`, `` ``, and `None` all abort.
    """
    if response is None:
        return "abort"
    cleaned = response.strip().lower()
    if cleaned == "y":
        return "proceed"
    return "abort"
