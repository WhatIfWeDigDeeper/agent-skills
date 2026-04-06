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
        """Model defaults to claude-opus-4-6 per SKILL.md Step 1 when --model is omitted."""
        result = parse_arguments("")
        assert result["model"] == "claude-opus-4-6"

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
