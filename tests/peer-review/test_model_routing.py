"""Tests for --model routing decisions in peer-review skill."""

from pathlib import Path

import pytest

from conftest import cli_output_parse_format, route_model

_SKILL_DIR = Path(__file__).resolve().parents[2] / "skills" / "peer-review"
_SKILL = _SKILL_DIR / "SKILL.md"
_CLI_INVOCATIONS = _SKILL_DIR / "references" / "cli-invocations.md"


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


class TestExternalCliOutputParseFormat:
    """All external CLIs are parsed via the prose path per cli-invocations.md Step 4e.

    Regression guard for issue #181: Step 3 sends copilot the same prose template
    (severity-grouped findings ending in `NO FINDINGS`) as codex, and Step
    4d invokes copilot without requesting JSON — so copilot output must be parsed
    as prose, not JSON. A JSON-parse path for copilot would always fall through to
    the raw-output fallback.
    """

    def test_copilot_parses_as_prose_not_json(self):
        assert cli_output_parse_format("copilot") == "prose"
        assert cli_output_parse_format("copilot:gpt-4o-mini") == "prose"

    def test_codex_parses_as_prose(self):
        assert cli_output_parse_format("codex") == "prose"

    def test_all_external_clis_share_one_parse_path(self):
        formats = {cli_output_parse_format(m) for m in ("copilot", "codex")}
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

    def test_reference_file_states_copilot_parsed_like_codex(self):
        """Step 4e must state copilot is parsed identically to codex as prose."""
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


class TestGeminiRemoved:
    """Gemini is no longer a supported route.

    Google discontinued the Gemini CLI (`@google/gemini-cli`) in favor of the
    Antigravity IDE, so `--model gemini` was removed rather than left pointing at
    an unmaintained binary. It must now fall through to the standard
    unsupported-model error, not route to a `gemini` binary.
    """

    @pytest.mark.parametrize("model", ["gemini", "gemini:gemini-2.0-flash", "GEMINI"])
    def test_gemini_raises_unsupported(self, model):
        with pytest.raises(ValueError, match="Unsupported --model value"):
            route_model(model)

    def test_error_message_does_not_advertise_gemini(self):
        with pytest.raises(ValueError) as exc_info:
            route_model("gemini")
        message = str(exc_info.value)
        assert "gemini[:submodel]" not in message
        for supported in ("self (default)", "claude-*", "copilot[:submodel]", "codex[:submodel]"):
            assert supported in message

    def test_skill_and_reference_files_do_not_mention_gemini(self):
        """No gemini invocation form or install hint may survive in the skill."""
        assert "gemini" not in _SKILL.read_text().lower()
        assert "gemini" not in _CLI_INVOCATIONS.read_text().lower()


class TestUnsupportedModelMessageConsistency:
    """Both copies of the error string in SKILL.md must agree with each other and the oracle.

    SKILL.md emits the message from two branches — the `claude-*` path (the
    assistant cannot select the requested model) and the external-CLI prefix
    check. A reader hitting one branch and a test asserting on the other must
    see the same supported-values list, so the two copies and `route_model`'s
    ValueError are pinned together here.
    """

    _SUPPORTED = (
        "Supported values: self (default), "
        "claude-* (if your assistant supports model selection), "
        "copilot[:submodel], codex[:submodel]."
    )

    def _skill_message_lines(self):
        return [
            line
            for line in _SKILL.read_text().splitlines()
            if "Unsupported --model value" in line
        ]

    def test_skill_has_exactly_two_copies(self):
        assert len(self._skill_message_lines()) == 2

    def test_both_skill_copies_use_the_same_supported_values(self):
        for line in self._skill_message_lines():
            assert self._SUPPORTED in line

    def test_skill_copies_match_the_route_model_oracle(self):
        with pytest.raises(ValueError) as exc_info:
            route_model("llama")
        assert self._SUPPORTED in str(exc_info.value)
