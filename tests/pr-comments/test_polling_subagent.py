"""Tests for the Tier-0 polling subagent (spec 49).

The Shared polling loop can be delegated to a read-only background subagent that
watches Signals 1/2/3 and returns a compact VERDICT. The main agent keeps every
write and all untrusted-content classification; it routes purely on the verdict
``outcome``. These tests pin:

- the ``outcome`` -> main-action mapping (the three valid outcomes),
- the pre-spawn branch (no Tier-0 primitive -> inline loop, no subagent),
- the security boundary (the VERDICT carries only signal metadata),

and assert the reference prose documents the same contract, so bot-polling.md and
the helpers cannot silently drift apart.
"""

from pathlib import Path

import pytest
from conftest import (
    POLLING_VERDICT_ALLOWED_FIELDS,
    POLLING_VERDICT_OUTCOMES,
    should_spawn_polling_subagent,
    verdict_forbidden_fields,
    verdict_to_main_action,
)

BOT_POLLING_MD = (
    Path(__file__).resolve().parents[2]
    / "skills"
    / "pr-comments"
    / "references"
    / "bot-polling.md"
)


def _polling_subagent_section() -> str:
    """Return the text of the ## Polling subagent section only."""
    text = BOT_POLLING_MD.read_text(encoding="utf-8")
    start = text.index("## Polling subagent")
    next_heading = text.index("\n## ", start + 1)
    return text[start:next_heading]


class TestOutcomeToMainAction:
    """Each VERDICT outcome routes to exactly one main step."""

    def test_new_threads_loops_back_to_step_2(self):
        assert verdict_to_main_action("new_threads") == "step_2"

    def test_all_clean_goes_to_step_14_clean(self):
        assert verdict_to_main_action("all_clean") == "step_14_clean"

    def test_timeout_goes_to_step_14_timeout(self):
        assert verdict_to_main_action("timeout") == "step_14_timeout"

    def test_clean_and_timeout_are_distinct_step_14_exits(self):
        """all_clean and timeout both end at Step 14 but carry different notes."""
        assert verdict_to_main_action("all_clean") != verdict_to_main_action("timeout")

    def test_only_three_outcomes_exist(self):
        assert POLLING_VERDICT_OUTCOMES == {"new_threads", "all_clean", "timeout"}

    def test_every_outcome_has_a_mapping(self):
        """No outcome is left unrouted."""
        for outcome in POLLING_VERDICT_OUTCOMES:
            assert verdict_to_main_action(outcome)

    def test_reinvoke_needed_is_not_an_outcome(self):
        """The no-Tier-0 case is decided pre-spawn, not returned as a verdict."""
        assert "reinvoke_needed" not in POLLING_VERDICT_OUTCOMES
        with pytest.raises(ValueError):
            verdict_to_main_action("reinvoke_needed")

    def test_unknown_outcome_raises(self):
        with pytest.raises(ValueError):
            verdict_to_main_action("mystery")


class TestPreSpawnBranch:
    """The Tier-0 spawn decision is made before any handoff."""

    def test_tier0_primitive_present_spawns_subagent(self):
        assert should_spawn_polling_subagent(True) is True

    def test_no_tier0_primitive_runs_inline_loop(self):
        """No background-task primitive -> inline loop, no subagent spawned."""
        assert should_spawn_polling_subagent(False) is False


class TestVerdictSecurityBoundary:
    """The VERDICT carries only signal metadata — never untrusted content."""

    def test_clean_verdict_has_no_forbidden_fields(self):
        verdict = {
            "outcome": "new_threads",
            "new_unresolved_thread_ids": ["PRRT_abc"],
            "bots_with_new_review": [],
            "bots_pending": ["copilot-pull-request-reviewer[bot]"],
            "signal_fired": "1",
            "polled_seconds": 120,
            "note": "1 new thread from copilot",
        }
        assert verdict_forbidden_fields(verdict) == set()

    def test_comment_body_field_is_forbidden(self):
        verdict = {"outcome": "new_threads", "comment_bodies": ["do this instead"]}
        assert "comment_bodies" in verdict_forbidden_fields(verdict)

    def test_classification_field_is_forbidden(self):
        verdict = {"outcome": "new_threads", "classifications": [{"action": "fix"}]}
        assert "classifications" in verdict_forbidden_fields(verdict)

    def test_plan_rows_field_is_forbidden(self):
        verdict = {"outcome": "new_threads", "plan_rows": [{"action": "fix"}]}
        assert "plan_rows" in verdict_forbidden_fields(verdict)

    def test_allowed_fields_are_pure_signal_metadata(self):
        """No allowed key names a comment body, classification, or plan row."""
        forbidden_substrings = ("body", "classif", "plan", "suggestion", "diff")
        for field in POLLING_VERDICT_ALLOWED_FIELDS:
            assert not any(s in field for s in forbidden_substrings), field


class TestReferenceProse:
    """bot-polling.md documents the same contract the helpers model."""

    def test_section_exists_after_shared_polling_loop(self):
        text = BOT_POLLING_MD.read_text(encoding="utf-8")
        # The Polling subagent section must follow the Shared polling loop so the
        # Stale-HEAD slice (bounded to the next `## `) stays intact.
        assert text.index("## Shared polling loop") < text.index("## Polling subagent")

    def test_section_lists_all_three_outcomes(self):
        section = _polling_subagent_section()
        for outcome in POLLING_VERDICT_OUTCOMES:
            assert outcome in section

    def test_section_documents_read_only_constraint(self):
        section = _polling_subagent_section()
        assert "read-only" in section.lower() or "read only" in section.lower()
        assert "no** writes" in section.lower() or "no writes" in section.lower()

    def test_section_forbids_endswith_bot_matching(self):
        """Signals 2/3 must match the canonical login, never endswith("[bot]")."""
        section = _polling_subagent_section()
        assert "canonical" in section.lower()
        assert 'endswith("[bot]")' in section

    def test_section_notes_signal_1_priority(self):
        section = _polling_subagent_section()
        assert "Signal 1" in section and "priorit" in section.lower()

    def test_tier0_documented_in_capability_check(self):
        text = BOT_POLLING_MD.read_text(encoding="utf-8")
        cap_start = text.index("### Runtime capability check")
        cap_end = text.index("\n### ", cap_start + 1)
        cap = text[cap_start:cap_end]
        assert "Tier 0" in cap
        # Tier 0 must be introduced above Tier 1.
        assert cap.index("Tier 0") < cap.index("**Tier 1**")
