"""Tests for Step 13 stale-HEAD bot detection ordering in pr-comments skill (#171).

The Stale-HEAD Bot Detection query compares against the PR's *remote* HEAD. If it
runs before ``git push``, the remote HEAD still points at the pre-push commit, so a
bot whose only activity was a clean approval at that prior HEAD is reported as
up-to-date and never re-requested. The fix runs the detection *after* ``git push``.

These tests assert the corrected ordering directly against SKILL.md prose, so they
would fail if the detection were moved back ahead of the push.
"""

from pathlib import Path

SKILL_MD = Path(__file__).resolve().parents[2] / "skills" / "pr-comments" / "SKILL.md"


def _step13_section() -> str:
    """Return the text of Step 13 up to (but not including) Step 13b."""
    text = SKILL_MD.read_text(encoding="utf-8")
    start = text.index("### 13. Push and Re-request Review")
    end = text.index("### 13b.", start)
    return text[start:end]


class TestStaleHeadDetectionAfterPush:
    """Step 13 must detect stale-HEAD bots only after the push has landed."""

    def test_run_site_is_after_push_not_in_list_building(self):
        """The query *run* instruction must follow `git push`, not sit in the
        reviewer-list-building prose that precedes it (the pre-fix location).

        Anchored on "Run the canonical query" — the actual run instruction, present
        both before and after the fix — so the test fails if the run site is moved
        back ahead of the push, which is exactly the #171 bug.
        """
        section = _step13_section()
        # The list-building paragraph ends where the manual-mode prompt begins.
        list_building = section[: section.index("If `--manual` was passed")]
        assert "Run the canonical query" not in list_building, (
            "Stale-HEAD Bot Detection must run after `git push`, not while building "
            "the reviewer list before the push (#171)."
        )
        push_idx = section.index("```bash\n   git push\n   ```")
        run_idx = section.index("Run the canonical query")
        assert push_idx < run_idx, (
            "Stale-HEAD Bot Detection must run after `git push` so the remote HEAD "
            "reflects the just-pushed commit (#171)."
        )

    def test_section_explains_why_detection_runs_after_push(self):
        """The rationale (remote HEAD / clean approval at prior HEAD) is documented."""
        section = _step13_section()
        assert "remote HEAD" in section
        assert "clean approval" in section

    def test_empty_commenter_list_still_reaches_push_when_commit_made(self):
        """An empty commenter list must not short-circuit before the push when a
        commit was made — otherwise stale-HEAD detection never runs."""
        section = _step13_section()
        # The skip-to-Step-14 guard must be conditioned on no commit, not on an
        # empty commenter list alone.
        assert "empty" in section
        assert "no commit was made in Step 10" in section


class TestBotPollingReferenceConsistency:
    """The reference file must document the post-push timing too."""

    def test_bot_polling_notes_after_push(self):
        ref = (
            SKILL_MD.parent / "references" / "bot-polling.md"
        ).read_text(encoding="utf-8")
        detection = ref[ref.index("## Stale-HEAD Bot Detection"):]
        assert "after" in detection and "git push" in detection
