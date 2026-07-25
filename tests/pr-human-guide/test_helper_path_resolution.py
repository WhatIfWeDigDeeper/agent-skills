"""Regression tests for marker-helper.py path resolution (issue #206).

Step 5 must not invoke the helper through a repo-root-relative `skills/...`
path — that path only exists in a checkout of the skills repo, and breaks for
every installed layout (.claude/skills/, .agents/skills/, ~/.claude/skills/,
plugin cache).
"""

from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[2] / "skills" / "pr-human-guide"
COMMANDS_MD = SKILL_DIR / "references" / "commands.md"


class TestHelperPathResolution:
    """The Step 5 invocation resolves the helper from the skill's own directory."""

    def test_no_repo_relative_invocation(self):
        assert "python3 skills/pr-human-guide" not in COMMANDS_MD.read_text()

    def test_invokes_resolved_helper_variable(self):
        assert 'python3 "$HELPER"' in COMMANDS_MD.read_text()

    def test_helper_derived_from_skill_dir(self):
        assert 'HELPER="$SKILL_DIR/references/marker-helper.py"' in COMMANDS_MD.read_text()

    def test_skill_dir_honors_environment_override(self):
        assert 'SKILL_DIR="${SKILL_DIR:-' in COMMANDS_MD.read_text()

    def test_guard_precedes_invocation(self):
        text = COMMANDS_MD.read_text()
        assert '[ -f "$HELPER" ]' in text
        assert text.index('[ -f "$HELPER" ]') < text.index('python3 "$HELPER"')

    def test_resolution_names_no_vendor_directory(self):
        """Portability: the distributed skill must not hardcode an assistant's layout."""
        text = COMMANDS_MD.read_text()
        for vendor in (".claude/skills", ".agents/skills", "~/.claude"):
            assert vendor not in text
