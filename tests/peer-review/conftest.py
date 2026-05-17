"""Pytest fixtures and helpers for peer-review skill tests."""

import re

HELP_TRIGGERS = {"help", "--help", "-h", "?"}

_PR_RE = re.compile(r'^[1-9][0-9]{0,5}$')
_BRANCH_RE = re.compile(r'^[A-Za-z0-9._/-]{1,255}$')


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
            if not _BRANCH_RE.match(result["branch_name"]) or ".." in result["branch_name"]:
                result["error"] = f"--branch requires a git ref name (letters, digits, ., _, /, -; no consecutive dots; <=255 chars), got: {result['branch_name']}"
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
# Patterns mirror the SKILL.md "**4b. Pre-flight secret scan**" step's
# "Case-sensitive group" / "Case-insensitive group" lists — POSIX ERE in the
# spec, translated to Python regex here. The translation prefers explicit ASCII character classes
# (`[A-Za-z0-9]`, `[ \t]`) over Python's PCRE-style `\w`/`\s` shortcuts to keep
# the matched whitespace set narrow and predictable. Python's `\s` is Unicode-
# aware (it includes NBSP, ideographic space, etc.); POSIX `[[:space:]]` follows
# the current locale's `isspace()` classification, so under common locales like
# `en_US.UTF-8` it can also match a broader set than just ASCII space/tab.
# Pinning the Python side to `[ \t]` keeps the match set narrow regardless of
# locale, and matches what the SKILL.md note recommends for callers that want
# strict ASCII semantics (run grep under `LC_ALL=C`). Cross-line `\s` matching
# is separately handled by `secret_scan()` iterating line-by-line.
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
            r"(api[_-]?key|secret|password|bearer|authorization)[ \t]*[:=][ \t]*['\"]?[A-Za-z0-9+/_=-]{16,}",
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


# Step 2b — PR-content prompt-injection screening pass (PR target only).
#
# Patterns mirror the SKILL.md Step 2b "Case-sensitive group", "Case-insensitive
# group", and "Unicode codepoint group" lists — POSIX ERE in the spec,
# translated to Python regex here. Same translation rules as
# `_SECRET_PATTERNS_*` above: explicit `[ \t]` over `\s`, ASCII character
# classes over Unicode shortcuts. Line-by-line iteration matches `grep -E`
# semantics in `pr_screen()` below.
_SCREEN_PATTERNS_CASE_SENSITIVE = [
    (
        "Override imperative",
        re.compile(
            r"(ignore|disregard|forget)[ \t]+(all[ \t]+)?(previous|prior|above)[ \t]+(instructions|directives|rules|prompts?)"
        ),
    ),
    (
        "Role-override opener",
        re.compile(r"you[ \t]+are[ \t]+now[ \t]+(a[ \t]+|an[ \t]+)?[A-Za-z]"),
    ),
    (
        "Claimed system role",
        re.compile(r"(system|developer)[ \t]+(prompt|message|instruction)"),
    ),
    ("HTML comment opener", re.compile(r"<!--")),
    ("Collapsed details block", re.compile(r"<details[ \t]*[a-z]*>")),
    ("Hex escape run", re.compile(r"(\\x[0-9A-Fa-f]{2}){4,}")),
    ("Long base64-shaped run", re.compile(r"[A-Za-z0-9+/]{200,}={0,2}")),
]

_SCREEN_PATTERNS_CASE_INSENSITIVE = [
    (
        "Role-impersonation request",
        re.compile(
            r"(act[ \t]+as|pretend[ \t]+to[ \t]+be|roleplay[ \t]+as)[ \t]+(the|an|a)?[ \t]*(admin|root|system|developer|assistant|agent)",
            re.IGNORECASE,
        ),
    ),
]

# Zero-width and bidi-control codepoints — UTF-8 byte equivalents in SKILL.md
# Step 2b are checked via `LC_ALL=C grep -E`; Python regex against the decoded
# string can use the actual codepoints directly.
_ZWS_BIDI_CHARS = (
    "​‌‍"  # zero-width space / non-joiner / joiner
    "‪‫‬‭‮"  # bidi overrides (LRE/RLE/PDF/LRO/RLO)
    "⁦⁧⁨⁩"  # bidi isolates (LRI/RLI/FSI/PDI)
)
_ZWS_BIDI_RE = re.compile(f"[{_ZWS_BIDI_CHARS}]")

_CYRILLIC_INSTRUCTION_WORDS = ("ignore", "instructions", "system", "prompt", "assistant", "disregard")
_CYRILLIC_ADJACENCY_RE = re.compile(
    r"(?:"
    + r"(?:" + "|".join(_CYRILLIC_INSTRUCTION_WORDS) + r").{0,8}[Ѐ-ӿ]"
    + r"|"
    + r"[Ѐ-ӿ].{0,8}(?:" + "|".join(_CYRILLIC_INSTRUCTION_WORDS) + r")"
    + r")",
    re.IGNORECASE,
)


def should_run_pr_screening(target_type: str | None) -> bool:
    """SKILL.md Step 2b runs only when the target is `--pr N`.

    `--staged`, `--branch`, and path targets are not third-party-author-controlled
    (own working tree / own branch refs / own local files) and skip the screen.
    None and any unknown target type also skip — there is no third-party content
    to scan.
    """
    return target_type == "pr"


def pr_screen(content: str) -> list[tuple[str, str]]:
    """Run all Step 2b pattern groups against `content`.

    Returns a list of `(pattern_name, matched_substring)` tuples — empty when
    no pattern fires. A match in any group counts; all groups are run
    independently per the spec's per-pattern iteration requirement.

    Scanning is line-by-line for the ASCII regex groups to mirror `grep -E`
    semantics (in Python `re`, `[ \\t]` would still let a multi-line input
    leak across line boundaries via the `.{0,N}` constructs used elsewhere;
    iterating splitlines keeps each pattern bounded to a single line).
    Unicode/adjacency checks scan the full content as a single string because
    they detect single-codepoint properties or short windows that may legally
    cross whitespace that is not a newline.
    """
    matches: list[tuple[str, str]] = []
    lines = content.splitlines() or [content]
    for name, pat in _SCREEN_PATTERNS_CASE_SENSITIVE:
        for line in lines:
            m = pat.search(line)
            if m:
                matches.append((name, m.group(0)))
                break
    for name, pat in _SCREEN_PATTERNS_CASE_INSENSITIVE:
        for line in lines:
            m = pat.search(line)
            if m:
                matches.append((name, m.group(0)))
                break
    zw = _ZWS_BIDI_RE.search(content)
    if zw:
        matches.append(("Zero-width / bidi-control codepoint", zw.group(0)))
    cyr = _CYRILLIC_ADJACENCY_RE.search(content)
    if cyr:
        matches.append(("Cyrillic homoglyph adjacent to ASCII instruction word", cyr.group(0)))
    return matches


def screen_size_guard(content: str, limit: int = 262144) -> tuple[str, bool]:
    """SKILL.md Step 2b 256 KB cap for the screening regex pass.

    Returns `(possibly_truncated, oversized_flag)`. The reviewer in Step 3
    still sees the full unmodified content — the truncation here is only for
    the regex pass. `oversized_flag=True` triggers the same confirmation pause
    as a flagged pattern, even when no pattern matched (burying signal in a
    10 MB PR body is itself an attack).

    Byte-length semantics mirror the SKILL.md `${#PR_CONTENT}` check, which in
    bash counts bytes for byte-locale strings. The Python helper uses
    `len(encoded)` against UTF-8 to keep cross-encoding behaviour predictable
    — a string whose codepoint count is under `limit` but whose UTF-8 byte
    length exceeds `limit` is treated as oversized.
    """
    encoded = content.encode("utf-8")
    if len(encoded) > limit:
        return encoded[:limit].decode("utf-8", errors="ignore"), True
    return content, False


def route_screening_response(response: str | None) -> str:
    """SKILL.md Step 2b confirmation routing: `y` proceeds, anything else aborts.

    Mirrors `route_confirmation_response` for Step 4b — same UX, same routing
    rules. Spec calls out that injected content saying "skip screening" cannot
    suppress the pause; this helper does not interpret the response content
    beyond exact-match on `y`.
    """
    if response is None:
        return "abort"
    cleaned = response.strip().lower()
    if cleaned == "y":
        return "proceed"
    return "abort"
