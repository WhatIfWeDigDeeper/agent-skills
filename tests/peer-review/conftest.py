"""Pytest fixtures and helpers for peer-review skill tests."""

HELP_TRIGGERS = {"help", "--help", "-h", "?"}


def is_help_request(args: str | None) -> bool:
    """Check if arguments are a help request per SKILL.md."""
    return args.strip().lower() in HELP_TRIGGERS if args and args.strip() else False


def parse_arguments(args: str | None) -> dict:
    """Parse peer-review arguments per SKILL.md.

    Returns:
        {
            "target_type": "staged" | "pr" | "branch" | "path" | None,
            "pr_number": str | None,
            "branch_name": str | None,
            "path": str | None,
            "model": str,  # Defaults to "claude-opus-4-6" on successful parses.
            "focus": str | None,
            "error": str | None,
        }
    """
    result = {
        "target_type": None,
        "pr_number": None,
        "branch_name": None,
        "path": None,
        "model": None,
        "focus": None,
        "error": None,
    }

    if not args or not args.strip():
        result["target_type"] = "staged"
        result["model"] = "claude-opus-4-6"
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
            i += 2

        elif tok == "--model":
            if i + 1 >= len(tokens):
                result["error"] = "--model requires a model name"
                return result
            result["model"] = tokens[i + 1]
            i += 2

        elif tok == "--focus":
            if i + 1 >= len(tokens):
                result["error"] = "--focus requires a topic"
                return result
            result["focus"] = tokens[i + 1]
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
        result["model"] = "claude-opus-4-6"

    return result


def detect_mode(has_plan_md: bool, has_tasks_md: bool) -> str:
    """Detect review mode from directory contents per SKILL.md.

    Returns: "spec" | "consistency"
    """
    if has_plan_md and has_tasks_md:
        return "spec"
    return "consistency"


def route_model(model: str | None) -> dict:
    """Determine reviewer route from --model value per SKILL.md Step 4.

    Returns:
        {
            "route": "claude" | "copilot" | "codex" | "gemini",
            "binary": str | None,  # CLI binary name (None for claude path)
            "submodel": str | None,  # Sub-model if specified after ':'
        }
    """
    if not model:
        return {"route": "claude", "binary": None, "submodel": None}

    model_lower = model.lower()
    if model_lower.startswith("claude-"):
        return {"route": "claude", "binary": None, "submodel": None}

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
        f"Unsupported --model value: '{model}'. Supported external CLIs: copilot, codex, gemini. "
        "For Claude models, use a claude-* prefix (e.g. --model claude-opus-4-6)."
    )
