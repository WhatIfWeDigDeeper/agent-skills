"""Tests for --model routing decisions in peer-review skill."""

from pathlib import Path

import pytest

from conftest import cli_output_parse_format, route_model

_CLI_INVOCATIONS = (
    Path(__file__).resolve().parents[2]
    / "skills"
    / "peer-review"
    / "references"
    / "cli-invocations.md"
)


class TestSelfAndClaudeRouting:
    """`self` and `claude-*` always route internally — all assistants handle Claude models natively."""

    def test_self_routes_to_internal(self):
        result = route_model("self")
        assert result["route"] == "internal"
        assert result["binary"] is None
        assert result["submodel"] is None

    def test_explicit_claude_model_routes_to_internal(self):
        result = route_model("claude-opus-4-6")
        assert result["route"] == "internal"
        assert result["binary"] is None
        assert result["submodel"] is None

    def test_any_claude_prefix_routes_to_internal(self):
        result = route_model("claude-haiku-4-5-20251001")
        assert result["route"] == "internal"
        assert result["binary"] is None

    def test_claude_sonnet_routes_to_internal(self):
        result = route_model("claude-sonnet-4-6")
        assert result["route"] == "internal"
        assert result["binary"] is None

    def test_empty_model_routes_to_internal(self):
        result = route_model("")
        assert result["route"] == "internal"

    def test_none_routes_to_internal(self):
        result = route_model(None)
        assert result["route"] == "internal"


class TestCopilotRouting:
    """--model copilot routes to the copilot binary."""

    def test_copilot_routes_to_copilot(self):
        result = route_model("copilot")
        assert result["route"] == "copilot"
        assert result["binary"] == "copilot"
        assert result["submodel"] is None

    def test_copilot_with_submodel(self):
        result = route_model("copilot:gpt-4o-mini")
        assert result["route"] == "copilot"
        assert result["binary"] == "copilot"
        assert result["submodel"] == "gpt-4o-mini"

    def test_copilot_with_different_submodel(self):
        result = route_model("copilot:gpt-4o")
        assert result["route"] == "copilot"
        assert result["submodel"] == "gpt-4o"


class TestCodexRouting:
    """--model codex routes to the codex binary."""

    def test_codex_routes_to_codex(self):
        result = route_model("codex")
        assert result["route"] == "codex"
        assert result["binary"] == "codex"
        assert result["submodel"] is None

    def test_codex_with_submodel(self):
        result = route_model("codex:gpt-4o")
        assert result["route"] == "codex"
        assert result["binary"] == "codex"
        assert result["submodel"] == "gpt-4o"


class TestGeminiRouting:
    """--model gemini routes to the gemini binary."""

    def test_gemini_routes_to_gemini(self):
        result = route_model("gemini")
        assert result["route"] == "gemini"
        assert result["binary"] == "gemini"
        assert result["submodel"] is None

    def test_gemini_with_submodel(self):
        result = route_model("gemini:gemini-2.0-flash")
        assert result["route"] == "gemini"
        assert result["binary"] == "gemini"
        assert result["submodel"] == "gemini-2.0-flash"


class TestExternalCliOutputParseFormat:
    """All external CLIs are parsed via the prose path per cli-invocations.md Step 4e.

    Regression guard for issue #181: Step 3 sends copilot the same prose template
    (severity-grouped findings ending in `NO FINDINGS`) as codex/gemini, and Step
    4d invokes copilot without requesting JSON — so copilot output must be parsed
    as prose, not JSON. A JSON-parse path for copilot would always fall through to
    the raw-output fallback.
    """

    def test_copilot_parses_as_prose_not_json(self):
        assert cli_output_parse_format("copilot") == "prose"
        assert cli_output_parse_format("copilot:gpt-4o-mini") == "prose"

    def test_codex_parses_as_prose(self):
        assert cli_output_parse_format("codex") == "prose"

    def test_gemini_parses_as_prose(self):
        assert cli_output_parse_format("gemini") == "prose"

    def test_all_external_clis_share_one_parse_path(self):
        formats = {cli_output_parse_format(m) for m in ("copilot", "codex", "gemini")}
        assert formats == {"prose"}, "external CLIs must share a single prose parse path"

    def test_internal_path_has_no_external_parse(self):
        assert cli_output_parse_format("self") is None
        assert cli_output_parse_format("claude-opus-4-6") is None

    def test_reference_file_does_not_claim_copilot_json_contract(self):
        """The Step 4e text must not describe a copilot-specific JSON output schema.

        Catches the #181 contradiction at the source: an earlier revision said
        copilot output is JSON `{ summary, overall_risk, findings: [...] }`, which
        contradicts the prose prompt the skill actually sends.
        """
        text = _CLI_INVOCATIONS.read_text()
        lowered = text.lower()
        assert "overall_risk" not in lowered
        assert "suggested_fix" not in lowered
        assert "output is json" not in lowered

    def test_reference_file_states_copilot_parsed_like_codex_gemini(self):
        """Step 4e must state copilot is parsed identically to codex/gemini as prose."""
        text = _CLI_INVOCATIONS.read_text().lower()
        assert "copilot" in text
        assert "markdown or plain text" in text


class TestUnsupportedModel:
    """Unsupported --model values raise ValueError rather than silently falling back to the internal path."""

    def test_unknown_prefix_raises(self):
        with pytest.raises(ValueError, match="Unsupported --model value"):
            route_model("llama")

    def test_unknown_prefix_with_submodel_raises(self):
        with pytest.raises(ValueError, match="Unsupported --model value"):
            route_model("gpt-4o:latest")
