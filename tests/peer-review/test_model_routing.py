"""Tests for --model routing decisions in peer-review skill."""

import pytest

from conftest import route_model


class TestSelfAndClaudeRouting:
    """`self` always routes internally; `claude-*` routes internally when `assistant == "claude"`."""

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


class TestNonClaudeEnvironment:
    """In non-Claude environments, claude-* routes to the claude CLI binary; self still routes internal."""

    def test_self_routes_to_internal_in_non_claude_env(self):
        result = route_model("self", assistant="copilot")
        assert result["route"] == "internal"
        assert result["binary"] is None

    def test_claude_model_routes_to_claude_binary_in_copilot_env(self):
        result = route_model("claude-opus-4-6", assistant="copilot")
        assert result["route"] == "claude"
        assert result["binary"] == "claude"
        assert result["submodel"] == "claude-opus-4-6"

    def test_claude_model_routes_to_claude_binary_in_gemini_env(self):
        result = route_model("claude-haiku-4-5-20251001", assistant="gemini")
        assert result["route"] == "claude"
        assert result["binary"] == "claude"
        assert result["submodel"] == "claude-haiku-4-5-20251001"

    def test_claude_model_routes_to_claude_binary_in_codex_env(self):
        result = route_model("claude-sonnet-4-6", assistant="codex")
        assert result["route"] == "claude"
        assert result["binary"] == "claude"

    def test_copilot_routes_normally_in_non_claude_env(self):
        result = route_model("copilot:gpt-4o", assistant="copilot")
        assert result["route"] == "copilot"
        assert result["submodel"] == "gpt-4o"


class TestUnsupportedModel:
    """Unsupported --model values raise ValueError rather than silently falling back to the internal path."""

    def test_unknown_prefix_raises(self):
        with pytest.raises(ValueError, match="Unsupported --model value"):
            route_model("llama")

    def test_unknown_prefix_with_submodel_raises(self):
        with pytest.raises(ValueError, match="Unsupported --model value"):
            route_model("gpt-4o:latest")
