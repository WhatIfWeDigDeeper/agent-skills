"""Regression tests for marker-helper.py path resolution (issue #206).

Step 5 must not invoke the helper through a repo-root-relative `skills/...`
path — that path only exists in a checkout of the skills repo, and breaks for
every installed layout (.claude/skills/, .agents/skills/, ~/.claude/skills/,
plugin cache).
"""

import re
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[2] / "skills" / "pr-human-guide"
COMMANDS_MD = SKILL_DIR / "references" / "commands.md"

# Install layouts a harness might be steered toward. None may appear in a file
# that ships with the skill — the resolution logic is layout-agnostic by design.
VENDOR_INSTALL_PATHS = (".claude/skills", ".agents/skills", "~/.claude")


def shipped_files():
    """Every text file distributed with the skill (SKILL.md + references/)."""
    paths = [SKILL_DIR / "SKILL.md"]
    paths += sorted(
        p
        for p in (SKILL_DIR / "references").iterdir()
        if p.is_file() and p.suffix in {".md", ".py"}
    )
    return paths


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

    def test_skill_dir_placeholder_disambiguates_from_references_dir(self):
        """`HELPER` appends `references/`, so SKILL_DIR must be its parent.

        Guidance that reads "the directory you read this file from" points at
        `references/` itself and yields `references/references/marker-helper.py`.
        """
        text = COMMANDS_MD.read_text()
        assert "parent of references/" in text
        assert "absolute path of the directory you read this file from" not in text

    def test_resolution_names_no_vendor_directory(self):
        """Portability: the distributed skill must not hardcode an assistant's layout."""
        text = COMMANDS_MD.read_text()
        for vendor in VENDOR_INSTALL_PATHS:
            assert vendor not in text


class TestShippedFilesArePortable:
    """Every file distributed with the skill, not just the one carrying Step 5.

    A vendor install path anywhere in the shipped tree can send a non-Claude
    harness looking under a directory that does not exist for it.
    """

    def test_no_shipped_file_names_a_vendor_install_path(self):
        offenders = []
        for path in shipped_files():
            text = path.read_text()
            for vendor in VENDOR_INSTALL_PATHS:
                if vendor in text:
                    offenders.append(f"{path.name}: {vendor}")
        assert not offenders, f"vendor install paths in shipped files: {offenders}"

    def test_assistant_names_appear_only_as_scoped_qualifiers(self):
        """A harness name must sit inside a parenthetical, never carry the instruction.

        `(e.g. in Claude Code: ...)` and `(in Claude Code: ...)` are the two forms
        the repo's Portability rules sanction.
        """
        offenders = []
        for path in shipped_files():
            for lineno, line in enumerate(path.read_text().splitlines(), 1):
                for match in re.finditer(r"Claude Code", line):
                    prefix = line[: match.start()]
                    if not re.search(r"\((?:e\.g\.\s+)?in $", prefix):
                        offenders.append(f"{path.name}:{lineno}: {line.strip()}")
        assert not offenders, f"unscoped assistant references: {offenders}"
