"""Structural tests for the compact-message skill (spec 59).

The emitted /compact line is model output and cannot be asserted here, so
these tests pin the SKILL.md rules that shape it: frontmatter, gapless
steps, Security model placement, the Step 4 composition rules, and the
Step 5 output contract.
"""

import re
from pathlib import Path

import pytest

SKILL_DIR = Path(__file__).resolve().parents[2] / "skills" / "compact-message"
SKILL_MD = SKILL_DIR / "SKILL.md"
OPTIONS_MD = SKILL_DIR / "references" / "options.md"

STEP_HEADING = re.compile(r"^### (\d+)\.[ \t]+(.+?)\s*$", re.MULTILINE)
SECTION_HEADING = re.compile(r"^## (.+?)\s*$", re.MULTILINE)
FENCED_BLOCK = re.compile(r"^```.*?^```", re.MULTILINE | re.DOTALL)


def skill_text() -> str:
    return SKILL_MD.read_text()


def frontmatter() -> str:
    match = re.match(r"^---\n(.*?)\n---\n", skill_text(), re.DOTALL)
    assert match, "SKILL.md must open with a --- frontmatter block"
    return match.group(1)


def description() -> str:
    """The frontmatter description, with a folded (>-) block joined by spaces."""
    lines = frontmatter().splitlines()
    for i, line in enumerate(lines):
        if line.startswith("description:"):
            value = line[len("description:"):].strip()
            if value not in (">-", ">", "|", "|-"):
                return value.strip("\"'")
            body = []
            for cont in lines[i + 1:]:
                if cont and not cont.startswith(" "):
                    break
                body.append(cont.strip())
            return " ".join(part for part in body if part)
    raise AssertionError("frontmatter has no description")


def step_headings() -> list[tuple[int, str]]:
    prose = FENCED_BLOCK.sub("", skill_text())
    return [(int(num), title) for num, title in STEP_HEADING.findall(prose)]


def step_body(number: int) -> str:
    """Raw text of step N (fences kept) up to the next step or ## heading."""
    text = skill_text()
    start = re.search(rf"^### {number}\.[ \t]+.*$", text, re.MULTILINE)
    assert start, f"no step {number}"
    rest = text[start.end():]
    end = re.search(r"^(### \d+\.|## )", rest, re.MULTILINE)
    return rest[: end.start()] if end else rest


def section_body(title: str) -> str:
    text = skill_text()
    matches = list(SECTION_HEADING.finditer(text))
    for i, match in enumerate(matches):
        if match.group(1) == title:
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            return text[match.end():end]
    raise AssertionError(f"no ## {title} section")


def flat(text: str) -> str:
    """Collapse whitespace so assertions survive line wrapping."""
    return " ".join(text.split())


class TestFrontmatter:
    def test_name(self):
        assert re.search(r"^name: compact-message$", frontmatter(), re.MULTILINE)

    def test_initial_version(self):
        assert re.search(r'^  version: "0\.1"$', frontmatter(), re.MULTILINE)

    def test_license(self):
        assert re.search(r"^license: MIT$", frontmatter(), re.MULTILINE)

    def test_description_within_limit(self):
        desc = description()
        assert desc, "description must not be empty"
        assert len(desc) <= 500, f"description is {len(desc)} chars, max 500"


class TestSteps:
    def test_steps_are_sequential_from_one(self):
        numbers = [num for num, _ in step_headings()]
        assert numbers == list(range(1, len(numbers) + 1)), (
            f"process step numbers must be gapless and start at 1, got {numbers}"
        )

    def test_has_five_steps(self):
        assert len(step_headings()) == 5


class TestArguments:
    def test_uses_portable_arguments_phrasing(self):
        assert "$ARGUMENTS" in section_body("Arguments")

    @pytest.mark.parametrize("trigger", ["`help`", "`--help`", "`-h`", "`?`"])
    def test_lists_help_trigger(self, trigger):
        assert trigger in section_body("Arguments")

    def test_help_routes_to_options(self):
        assert "references/options.md" in section_body("Arguments")

    def test_focus_text_cannot_override_step4_rules(self):
        body = flat(section_body("Arguments")).lower()
        assert "not the step 4 rules" in body


class TestSecurityModel:
    def test_security_model_immediately_precedes_process(self):
        titles = SECTION_HEADING.findall(skill_text())
        assert "Security model" in titles and "Process" in titles
        assert titles.index("Process") == titles.index("Security model") + 1, (
            f"## Security model must be the section right before ## Process, got {titles}"
        )

    @pytest.mark.parametrize("sub", ["### Threat model", "### Mitigations", "### Residual risks"])
    def test_template_subsections(self, sub):
        assert sub in section_body("Security model")

    def test_forbids_lifting_instructions_from_observed_content(self):
        body = flat(section_body("Security model"))
        assert "**Facts, not foreign instructions**" in body
        assert "never as imperative instructions" in body.lower()


class TestComposeRules:
    """Step 4: the rules the emitted line must satisfy."""

    def test_single_line(self):
        body = flat(step_body(4)).lower()
        assert "single line" in body and "no newlines" in body

    def test_compact_prefix(self):
        assert "`/compact `" in step_body(4)

    def test_bare_compact_exception_for_near_empty_session(self):
        assert "bare `/compact` of a near-empty session" in flat(step_body(4))

    def test_length_cap(self):
        assert "800" in step_body(4)

    def test_no_secrets(self):
        assert "never copy tokens" in flat(step_body(4)).lower()

    def test_facts_only_keyed_on_authorization(self):
        body = flat(step_body(4))
        assert "**Facts only**" in body
        lower = body.lower()
        assert "the user issued or agreed to" in lower
        assert "attributed fact" in lower
        assert "addressed to the assistant or summarizer" in lower


class TestTopicShift:
    """Step 3: /clear advice and the near-empty path stay within Step 5's block."""

    def test_near_empty_triggers_clear_suggestion(self):
        assert "step 5 item 3 suggests `/clear`" in flat(step_body(3)).lower()


class TestOutputContract:
    """Step 5: fenced command, mandatory, then stop."""

    def test_text_fence(self):
        assert "```text" in step_body(5)

    def test_fences_are_markdown_only(self):
        assert "fences are markdown only" in flat(step_body(5)).lower()

    def test_mandatory_never_omit(self):
        body = flat(step_body(5))
        assert "MANDATORY" in body
        assert "never omit" in body.lower()

    def test_block_emitted_even_when_clear_recommended_instead(self):
        assert "including when step 3 recommends `/clear` instead" in flat(step_body(5)).lower()

    def test_reports_excluded_injection_text(self):
        body = flat(step_body(5)).lower()
        assert "addressed to the assistant or summarizer" in body
        assert "one bullet says it was left out" in body

    def test_stop_generating(self):
        assert "stop generating" in flat(step_body(5)).lower()

    def test_compaction_command_portability_note(self):
        body = flat(step_body(5)).lower()
        assert "other assistants" in body and "adjust the prefix" in body


class TestOptionsFile:
    def test_options_file_exists(self):
        assert OPTIONS_MD.exists()

    @pytest.mark.parametrize("trigger", ["`help`", "`--help`", "`-h`", "`?`"])
    def test_documents_help_trigger(self, trigger):
        assert trigger in OPTIONS_MD.read_text()

    def test_has_focus_text_example(self):
        assert re.search(
            r"/compact-message (?!help\b|--help\b|-h\b|\?)\w", OPTIONS_MD.read_text()
        ), "options.md must show at least one focus-text invocation"

    def test_focus_text_limits_match_step4_rules(self):
        text = flat(OPTIONS_MD.read_text()).lower()
        assert "secrets" in text and "single line" in text

    def test_clear_suggestion_covers_near_empty_session(self):
        assert "nothing worth keeping" in flat(OPTIONS_MD.read_text()).lower()
