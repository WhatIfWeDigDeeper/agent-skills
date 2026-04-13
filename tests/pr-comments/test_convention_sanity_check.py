"""Tests for Step 6 convention-rule sanity-check in pr-comments skill."""

from conftest import (
    classify_convention_suggestion,
    has_normative_language,
    is_convention_file,
    triggers_convention_sanity_check,
)


class TestIsConventionFile:
    """Test detection of instructions/conventions file targets."""

    def test_claude_md_is_convention_file(self):
        assert is_convention_file("CLAUDE.md") is True

    def test_nested_claude_md_is_convention_file(self):
        assert is_convention_file(".github/CLAUDE.md") is True

    def test_copilot_instructions_is_convention_file(self):
        assert is_convention_file(".github/copilot-instructions.md") is True

    def test_agents_md_is_convention_file(self):
        assert is_convention_file("AGENTS.md") is True

    def test_custom_instructions_file_is_convention_file(self):
        assert is_convention_file("docs/project-instructions.md") is True

    def test_skill_md_is_not_convention_file(self):
        assert is_convention_file("skills/pr-comments/SKILL.md") is False

    def test_readme_is_not_convention_file(self):
        assert is_convention_file("README.md") is False

    def test_python_file_is_not_convention_file(self):
        assert is_convention_file("tests/pr-comments/conftest.py") is False

    def test_benchmark_json_is_not_convention_file(self):
        assert is_convention_file("evals/pr-comments/benchmark.json") is False


class TestHasNormativeLanguage:
    """Test detection of normative language in comment bodies."""

    def test_must_triggers(self):
        assert has_normative_language("All test files must be skill-prefixed.") is True

    def test_always_triggers(self):
        assert has_normative_language("You should always add a trailing comma.") is True

    def test_convention_requires_triggers(self):
        assert has_normative_language("Convention requires skill-prefixed names.") is True

    def test_convention_is_triggers(self):
        assert has_normative_language("The convention is to use snake_case.") is True

    def test_should_always_triggers(self):
        assert has_normative_language("should always include a trap cleanup") is True

    def test_all_must_triggers(self):
        assert has_normative_language("All benchmark files must include a delta field.") is True

    def test_all_should_triggers(self):
        assert has_normative_language("All PR descriptions should mention settings changes.") is True

    def test_case_insensitive(self):
        assert has_normative_language("MUST be prefixed.") is True

    def test_plain_suggestion_no_trigger(self):
        assert has_normative_language("Consider adding a null check before this call.") is False

    def test_question_no_trigger(self):
        assert has_normative_language("Could this cause an issue with existing tests?") is False

    def test_general_feedback_no_trigger(self):
        assert has_normative_language("This looks good, nice work.") is False


class TestTriggersConventionSanityCheck:
    """Test the combined trigger: convention file + normative language."""

    def test_convention_file_target_detected(self):
        """CLAUDE.md targeted with 'must' language triggers the sanity-check."""
        comment = {
            "path": "CLAUDE.md",
            "body": "All test files must be skill-prefixed to avoid import collisions.",
        }
        assert triggers_convention_sanity_check(comment) is True

    def test_copilot_instructions_with_normative_language(self):
        comment = {
            "path": ".github/copilot-instructions.md",
            "body": "Convention requires test files to be prefixed with the skill name.",
        }
        assert triggers_convention_sanity_check(comment) is True

    def test_convention_file_without_normative_language(self):
        """A suggestion targeting CLAUDE.md with a plain code change doesn't trigger."""
        comment = {
            "path": "CLAUDE.md",
            "body": "Consider removing the trailing whitespace on line 42.",
        }
        assert triggers_convention_sanity_check(comment) is False

    def test_normative_language_on_non_convention_file(self):
        """'Must' language in a SKILL.md comment is not a convention sanity-check."""
        comment = {
            "path": "skills/pr-comments/SKILL.md",
            "body": "This step must always run before the commit.",
        }
        assert triggers_convention_sanity_check(comment) is False

    def test_code_file_normative_language_no_trigger(self):
        comment = {
            "path": "tests/pr-comments/conftest.py",
            "body": "This function must return a boolean.",
        }
        assert triggers_convention_sanity_check(comment) is False


class TestClassifyConventionSuggestion:
    """Test the decision logic after the counter-example search."""

    def test_no_counter_examples_fix_unchanged(self):
        """0 counter-examples: classify as fix normally."""
        result = classify_convention_suggestion(counter_example_count=0, can_soften=True)
        assert result["action"] == "fix"
        assert result["softened"] is False

    def test_one_counter_example_fix_unchanged(self):
        """1 counter-example (the file being changed): classify as fix normally."""
        result = classify_convention_suggestion(counter_example_count=1, can_soften=True)
        assert result["action"] == "fix"
        assert result["softened"] is False

    def test_counter_examples_found_soften(self):
        """>=2 counter-examples and can soften: fix with softened wording."""
        result = classify_convention_suggestion(counter_example_count=2, can_soften=True)
        assert result["action"] == "fix"
        assert result["softened"] is True

    def test_counter_examples_many_soften(self):
        result = classify_convention_suggestion(counter_example_count=5, can_soften=True)
        assert result["action"] == "fix"
        assert result["softened"] is True

    def test_counter_examples_found_decline(self):
        """>=2 counter-examples, cannot soften: decline."""
        result = classify_convention_suggestion(counter_example_count=2, can_soften=False)
        assert result["action"] == "decline"
        assert result["softened"] is False

    def test_counter_examples_many_decline(self):
        result = classify_convention_suggestion(counter_example_count=10, can_soften=False)
        assert result["action"] == "decline"
        assert result["softened"] is False

    def test_boundary_exactly_two(self):
        """Exactly 2 counter-examples crosses the >= 2 threshold."""
        result_soften = classify_convention_suggestion(counter_example_count=2, can_soften=True)
        result_decline = classify_convention_suggestion(counter_example_count=2, can_soften=False)
        assert result_soften["action"] == "fix"
        assert result_soften["softened"] is True
        assert result_decline["action"] == "decline"
