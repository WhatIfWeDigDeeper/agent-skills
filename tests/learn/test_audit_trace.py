"""Structural tests for the learn skill's min-char audit trace (spec 54).

Issues #211 / #217: the audit was mandatory in wording but emitted no
artifact, so a skipped audit was indistinguishable from one that ran.
Spec 54 promotes it to its own numbered step and adds a ``Cut in audit:``
field to the plan template. These tests parse the real SKILL.md so the
step numbering and the template field cannot drift silently.
"""

import re
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[2] / "skills" / "learn"
SKILL_MD = SKILL_DIR / "SKILL.md"
MULTICONFIG_MD = SKILL_DIR / "references" / "multiconfig-routing.md"

# ``### N. Title`` process steps. Fenced blocks are stripped first: the
# Route C skill template embeds a literal ``### 1. [First Step]`` that is
# example content, not a process step.
STEP_HEADING = re.compile(r"^### (\d+)\.[ \t]+(.+?)\s*$", re.MULTILINE)
FENCED_BLOCK = re.compile(r"^```.*?^```", re.MULTILINE | re.DOTALL)


def prose() -> str:
    """SKILL.md with fenced code blocks removed."""
    return FENCED_BLOCK.sub("", SKILL_MD.read_text())


def step_headings() -> list[tuple[int, str]]:
    """All ``### N. Title`` process steps as (number, title) pairs."""
    return [(int(num), title) for num, title in STEP_HEADING.findall(prose())]


def step_number(title_fragment: str) -> int:
    for num, title in step_headings():
        if title_fragment in title:
            return num
    raise AssertionError(f"no step titled {title_fragment!r}: {step_headings()}")


def step_body(title_fragment: str) -> str:
    text = prose()
    matches = list(STEP_HEADING.finditer(text))
    for i, match in enumerate(matches):
        if title_fragment in match.group(2):
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            return text[match.end() : end]
    raise AssertionError(f"no step titled {title_fragment!r}")


class TestStepNumbering:
    """Spec 54 Change 2: the audit is its own numbered step."""

    def test_steps_are_sequential_from_one(self):
        numbers = [num for num, _ in step_headings()]
        assert numbers == list(range(1, len(numbers) + 1)), (
            f"process step numbers must be gapless and start at 1, got {numbers}"
        )

    def test_audit_step_exists(self):
        assert step_number("Audit Rule Text") > 0

    def test_audit_step_precedes_plan_step(self):
        assert step_number("Audit Rule Text") < step_number("Present Plan")

    def test_old_preamble_audit_sentence_is_gone(self):
        # Anchor on the removed paragraph's distinctive opener, not on its closing
        # "the audit is not optional" — that phrase is generic enough to reappear
        # legitimately elsewhere and false-fail this test. "Before showing the plan"
        # alone is not usable either: it still opens the dedup sentence in Present Plan.
        assert "audit each drafted rule body" not in SKILL_MD.read_text(), (
            "the preamble audit paragraph should have been replaced by the numbered step"
        )


class TestAuditStepContent:
    """Spec 54 Change 1: the procedure is per-clause and names its artifact."""

    def test_audit_step_names_the_split_boundary(self):
        assert "em-dash" in step_body("Audit Rule Text")

    def test_audit_step_points_at_the_plan_field(self):
        assert "Cut in audit" in step_body("Audit Rule Text")

    def test_audit_step_carries_the_skipped_signal(self):
        """Issue #217's falsifiable self-check."""
        assert "was skipped" in step_body("Audit Rule Text")

    def test_audit_step_has_no_hardcoded_forward_step_number(self):
        """A hardcoded 'Step 6' would drift on the next step insertion."""
        assert not re.search(r"Step \d", step_body("Audit Rule Text"))


class TestPlanTemplate:
    """Spec 54 Change 3: the audit leaves a trace the user can reject."""

    def test_template_has_cut_in_audit_field(self):
        assert "- Cut in audit:" in SKILL_MD.read_text()

    def test_cut_in_audit_precedes_destination(self):
        content = SKILL_MD.read_text()
        assert content.index("- Cut in audit:") < content.index("- Destination:")


class TestCrossReferences:
    """Spec 54 Change 4: references track the renumbered plan step."""

    def test_multiconfig_routing_points_at_current_plan_step(self):
        expected = step_number("Present Plan")
        text = " ".join(MULTICONFIG_MD.read_text().split())
        assert f"Step {expected} confirmation" in text, (
            f"multiconfig-routing.md must reference Step {expected} confirmation"
        )
