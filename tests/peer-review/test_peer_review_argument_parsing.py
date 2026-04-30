"""Tests for argument parsing in peer-review skill."""

from conftest import parse_arguments


class TestNoArguments:
    """No arguments triggers auto-detect (explicit_staged=False); target_type defaults to staged."""

    def test_empty_string(self):
        result = parse_arguments("")
        assert result["target_type"] == "staged"
        assert result["error"] is None

    def test_none(self):
        result = parse_arguments(None)
        assert result["target_type"] == "staged"
        assert result["error"] is None

    def test_whitespace_only(self):
        result = parse_arguments("   ")
        assert result["target_type"] == "staged"
        assert result["error"] is None


class TestStagedTarget:
    """--staged sets target to staged (staged-only, explicit_staged=True; skips auto-detection)."""

    def test_staged_flag(self):
        result = parse_arguments("--staged")
        assert result["target_type"] == "staged"
        assert result["error"] is None

    def test_staged_with_model(self):
        result = parse_arguments("--staged --model claude-haiku-4-5-20251001")
        assert result["target_type"] == "staged"
        assert result["model"] == "claude-haiku-4-5-20251001"
        assert result["error"] is None

    def test_staged_with_focus(self):
        result = parse_arguments("--staged --focus security")
        assert result["target_type"] == "staged"
        assert result["focus"] == "security"
        assert result["error"] is None

    def test_explicit_staged_sets_flag(self):
        """--staged explicitly given sets explicit_staged=True."""
        result = parse_arguments("--staged")
        assert result["explicit_staged"] is True

    def test_no_args_does_not_set_explicit_staged(self):
        """No target leaves explicit_staged=False (auto-detect applies)."""
        result = parse_arguments("")
        assert result["explicit_staged"] is False

    def test_none_does_not_set_explicit_staged(self):
        result = parse_arguments(None)
        assert result["explicit_staged"] is False

    def test_options_only_do_not_set_explicit_staged(self):
        """Non-target options alone keep explicit_staged=False."""
        result = parse_arguments(
            "--model claude-haiku-4-5-20251001 --focus security"
        )
        assert result["target_type"] == "staged"
        assert result["model"] == "claude-haiku-4-5-20251001"
        assert result["focus"] == "security"
        assert result["explicit_staged"] is False
        assert result["error"] is None


class TestPRTarget:
    """--pr N sets target to PR with number."""

    def test_pr_with_number(self):
        result = parse_arguments("--pr 42")
        assert result["target_type"] == "pr"
        assert result["pr_number"] == "42"
        assert result["error"] is None

    def test_pr_with_focus(self):
        result = parse_arguments("--pr 99 --focus consistency")
        assert result["target_type"] == "pr"
        assert result["pr_number"] == "99"
        assert result["focus"] == "consistency"
        assert result["error"] is None

    def test_pr_with_model_override(self):
        result = parse_arguments("--pr 5 --model claude-haiku-4-5-20251001")
        assert result["target_type"] == "pr"
        assert result["pr_number"] == "5"
        assert result["model"] == "claude-haiku-4-5-20251001"
        assert result["error"] is None


class TestBranchTarget:
    """--branch NAME sets target to branch diff."""

    def test_branch_with_name(self):
        result = parse_arguments("--branch feat/my-feature")
        assert result["target_type"] == "branch"
        assert result["branch_name"] == "feat/my-feature"
        assert result["error"] is None

    def test_branch_with_focus(self):
        result = parse_arguments("--branch main --focus evals")
        assert result["target_type"] == "branch"
        assert result["branch_name"] == "main"
        assert result["focus"] == "evals"
        assert result["error"] is None


class TestPathTarget:
    """A bare path token sets target to file/directory."""

    def test_file_path(self):
        result = parse_arguments("specs/16-peer-review")
        assert result["target_type"] == "path"
        assert result["path"] == "specs/16-peer-review"
        assert result["error"] is None

    def test_path_with_focus(self):
        result = parse_arguments("skills/pr-comments/ --focus consistency")
        assert result["target_type"] == "path"
        assert result["path"] == "skills/pr-comments/"
        assert result["focus"] == "consistency"
        assert result["error"] is None

    def test_path_with_model(self):
        result = parse_arguments("src/api.ts --model claude-opus-4-6")
        assert result["target_type"] == "path"
        assert result["path"] == "src/api.ts"
        assert result["model"] == "claude-opus-4-6"
        assert result["error"] is None


class TestConflictDetection:
    """Mutually exclusive target selectors produce an error."""

    def test_staged_and_pr(self):
        result = parse_arguments("--staged --pr 42")
        assert result["error"] is not None
        assert "mutually exclusive" in result["error"]

    def test_staged_and_branch(self):
        result = parse_arguments("--staged --branch main")
        assert result["error"] is not None
        assert "mutually exclusive" in result["error"]

    def test_staged_and_path(self):
        result = parse_arguments("--staged specs/16-peer-review")
        assert result["error"] is not None
        assert "mutually exclusive" in result["error"]

    def test_pr_and_branch(self):
        result = parse_arguments("--pr 42 --branch main")
        assert result["error"] is not None
        assert "mutually exclusive" in result["error"]

    def test_pr_and_path(self):
        result = parse_arguments("--pr 42 specs/16-peer-review")
        assert result["error"] is not None
        assert "mutually exclusive" in result["error"]

    def test_two_paths(self):
        result = parse_arguments("specs/16-peer-review skills/peer-review")
        assert result["error"] is not None
        assert "mutually exclusive" in result["error"]


class TestOptions:
    """Options --model and --focus are parsed correctly."""

    def test_default_model_is_reviewer_default(self):
        """Model defaults to self per SKILL.md Step 1 when --model is omitted."""
        result = parse_arguments("")
        assert result["model"] == "self"

    def test_model_override(self):
        result = parse_arguments("--model claude-opus-4-6")
        assert result["model"] == "claude-opus-4-6"
        assert result["target_type"] == "staged"

    def test_focus_topic(self):
        result = parse_arguments("--focus security")
        assert result["focus"] == "security"
        assert result["target_type"] == "staged"

    def test_model_and_focus_together(self):
        result = parse_arguments("--model claude-opus-4-6 --focus consistency")
        assert result["model"] == "claude-opus-4-6"
        assert result["focus"] == "consistency"
        assert result["target_type"] == "staged"


class TestArgumentValidation:
    """--pr and --branch values are validated against regex rules per SKILL.md."""

    def test_pr_valid_integer(self):
        result = parse_arguments("--pr 42")
        assert result["error"] is None
        assert result["pr_number"] == "42"

    def test_pr_valid_large(self):
        result = parse_arguments("--pr 9999")
        assert result["error"] is None

    def test_pr_invalid_zero(self):
        result = parse_arguments("--pr 0")
        assert result["error"] is not None
        assert "--pr requires a positive integer" in result["error"]
        assert "0" in result["error"]

    def test_pr_invalid_negative(self):
        result = parse_arguments("--pr -1")
        assert result["error"] is not None
        assert "--pr requires a positive integer" in result["error"]

    def test_pr_invalid_shell_injection(self):
        result = parse_arguments("--pr 1;echo")
        assert result["error"] is not None
        assert "--pr requires a positive integer" in result["error"]

    def test_pr_invalid_alpha(self):
        result = parse_arguments("--pr abc")
        assert result["error"] is not None
        assert "--pr requires a positive integer" in result["error"]

    def test_branch_valid_simple(self):
        result = parse_arguments("--branch main")
        assert result["error"] is None
        assert result["branch_name"] == "main"

    def test_branch_valid_with_slash(self):
        result = parse_arguments("--branch feat/my-feature")
        assert result["error"] is None

    def test_branch_valid_with_dots_and_underscores(self):
        result = parse_arguments("--branch release_1.0")
        assert result["error"] is None

    def test_branch_invalid_semicolon(self):
        result = parse_arguments("--branch main;rm")
        assert result["error"] is not None
        assert "--branch requires a git ref name" in result["error"]

    def test_branch_invalid_metachar_in_name(self):
        # whitespace splits tokens so spaces can't survive as one token;
        # test an ampersand metachar that does survive as one token
        result = parse_arguments("--branch main&evil")
        assert result["error"] is not None
        assert "--branch requires a git ref name" in result["error"]

    def test_branch_invalid_dollar_sign(self):
        result = parse_arguments("--branch $HOME")
        assert result["error"] is not None
        assert "--branch requires a git ref name" in result["error"]

    def test_focus_invalid_no_topic(self):
        result = parse_arguments("--focus")
        assert result["error"] is not None
        assert "--focus requires a non-empty topic" in result["error"]

    def test_focus_invalid_trailing_no_topic(self):
        result = parse_arguments("--staged --focus")
        assert result["error"] is not None
        assert "--focus requires a non-empty topic" in result["error"]

    def test_focus_valid_topic(self):
        result = parse_arguments("--focus security")
        assert result["error"] is None
        assert result["focus"] == "security"

    def test_focus_invalid_empty_topic(self):
        result = parse_arguments(["--focus", ""])
        assert result["error"] is not None
        assert "--focus requires a non-empty topic" in result["error"]

    def test_focus_invalid_whitespace_topic(self):
        result = parse_arguments(["--focus", "   "])
        assert result["error"] is not None
        assert "--focus requires a non-empty topic" in result["error"]
