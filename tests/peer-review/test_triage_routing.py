"""Tests for triage layer routing and re-scan behavior in peer-review skill."""

import pytest

from conftest import route_model


def uses_triage(model: str | None) -> bool:
    """Return True if the model routes through the external CLI path (triage activates).

    Triage only activates on the external CLI path (copilot, codex, gemini).
    The Claude path never triggers triage.
    """
    result = route_model(model)
    return result["route"] in ("copilot", "codex", "gemini")


def parse_triage_output(triage_output: str, finding_count: int) -> dict:
    """Parse triage subagent output into recommend/skip buckets per SKILL.md Step 4e.

    Returns:
        {
            "recommended": list[int],   # 1-indexed finding numbers classified as recommend
            "skipped": dict[int, str],  # 1-indexed finding number -> skip reason
            "parse_failed": bool,       # True if output could not be parsed
        }
    """
    recommended = []
    skipped = {}
    found_any = False

    for line in triage_output.strip().splitlines():
        line = line.strip()
        if not line.startswith("FINDING "):
            continue
        try:
            rest = line[len("FINDING "):]
            colon_idx = rest.index(":")
            n = int(rest[:colon_idx].strip())
            verdict = rest[colon_idx + 1:].strip()
            found_any = True
            if verdict.lower().startswith("recommend"):
                recommended.append(n)
            elif verdict.lower().startswith("skip"):
                reason = ""
                if "\u2014" in verdict:
                    reason = verdict.split("\u2014", 1)[1].strip()
                elif "—" in verdict:
                    reason = verdict.split("—", 1)[1].strip()
                elif "-" in verdict:
                    reason = verdict.split("-", 1)[1].strip()
                skipped[n] = reason
        except (ValueError, IndexError):
            continue

    parse_failed = not found_any
    if parse_failed:
        # Fallback: treat all as recommended
        recommended = list(range(1, finding_count + 1))

    return {
        "recommended": recommended,
        "skipped": skipped,
        "parse_failed": parse_failed,
    }


class TestTriageActivation:
    """Triage activates only on the external CLI path."""

    def test_claude_path_no_triage(self):
        assert uses_triage("claude-opus-4-6") is False

    def test_claude_path_default_no_triage(self):
        assert uses_triage(None) is False

    def test_copilot_triggers_triage(self):
        assert uses_triage("copilot") is True

    def test_codex_triggers_triage(self):
        assert uses_triage("codex") is True

    def test_gemini_triggers_triage(self):
        assert uses_triage("gemini") is True

    def test_copilot_with_submodel_triggers_triage(self):
        assert uses_triage("copilot:gpt-4o-mini") is True

    def test_gemini_with_submodel_triggers_triage(self):
        assert uses_triage("gemini:gemini-2.0-flash") is True


class TestTriageOutputParsing:
    """Parse triage subagent output into recommend/skip buckets."""

    def test_all_recommend(self):
        output = "FINDING 1: recommend\nFINDING 2: recommend"
        result = parse_triage_output(output, 2)
        assert result["recommended"] == [1, 2]
        assert result["skipped"] == {}
        assert result["parse_failed"] is False

    def test_all_skip(self):
        output = "FINDING 1: skip \u2014 speculative opinion\nFINDING 2: skip \u2014 already documented"
        result = parse_triage_output(output, 2)
        assert result["recommended"] == []
        assert 1 in result["skipped"]
        assert 2 in result["skipped"]
        assert result["parse_failed"] is False

    def test_mixed_recommend_skip(self):
        output = "FINDING 1: recommend\nFINDING 2: skip \u2014 contradicts verified content"
        result = parse_triage_output(output, 2)
        assert result["recommended"] == [1]
        assert 2 in result["skipped"]
        assert result["parse_failed"] is False

    def test_parse_failed_fallback_treats_all_as_recommended(self):
        output = "Could not classify any findings."
        result = parse_triage_output(output, 3)
        assert result["parse_failed"] is True
        assert result["recommended"] == [1, 2, 3]
        assert result["skipped"] == {}

    def test_empty_output_fallback(self):
        result = parse_triage_output("", 2)
        assert result["parse_failed"] is True
        assert result["recommended"] == [1, 2]

    def test_skip_reason_extracted(self):
        output = "FINDING 1: skip \u2014 already handled in the reviewed content"
        result = parse_triage_output(output, 1)
        assert "already handled" in result["skipped"][1]

    def test_skip_with_dash_separator(self):
        output = "FINDING 1: skip - speculative opinion without evidence"
        result = parse_triage_output(output, 1)
        assert 1 in result["skipped"]
        assert result["parse_failed"] is False


class TestRescanOfferConditions:
    """Re-scan offer fires after apply, not after skip."""

    def should_offer_rescan(self, files_modified: int, user_replied_skip: bool, is_rescan_cycle: bool) -> bool:
        """Return True if re-scan offer should be shown per SKILL.md Step 6 rules."""
        if user_replied_skip:
            return False
        if is_rescan_cycle:
            return False
        return files_modified >= 1

    def test_rescan_offered_after_apply_with_modifications(self):
        assert self.should_offer_rescan(files_modified=1, user_replied_skip=False, is_rescan_cycle=False) is True

    def test_rescan_offered_after_multiple_modifications(self):
        assert self.should_offer_rescan(files_modified=3, user_replied_skip=False, is_rescan_cycle=False) is True

    def test_rescan_not_offered_after_skip(self):
        assert self.should_offer_rescan(files_modified=0, user_replied_skip=True, is_rescan_cycle=False) is False

    def test_rescan_not_offered_when_no_files_modified(self):
        assert self.should_offer_rescan(files_modified=0, user_replied_skip=False, is_rescan_cycle=False) is False

    def test_rescan_not_offered_during_rescan_cycle(self):
        assert self.should_offer_rescan(files_modified=2, user_replied_skip=False, is_rescan_cycle=True) is False


class TestSPrefixSelection:
    """S-prefix numbers refer to skipped findings; plain numbers refer to recommended."""

    def resolve_selection(self, user_reply: str, recommended: list[int], skipped_keys: list[int]) -> dict:
        """Map a user reply string to which findings to apply.

        Returns:
            {
                "recommended_to_apply": list[int],
                "skipped_to_apply": list[int],
                "skip_all": bool,
            }
        """
        user_reply = user_reply.strip().lower()
        if user_reply == "skip":
            return {"recommended_to_apply": [], "skipped_to_apply": [], "skip_all": True}

        if user_reply == "all":
            return {"recommended_to_apply": list(recommended), "skipped_to_apply": [], "skip_all": False}

        rec_apply = []
        skip_apply = []
        for token in user_reply.split(","):
            token = token.strip()
            if token.startswith("s") and token[1:].isdigit():
                n = int(token[1:])
                if n in skipped_keys:
                    skip_apply.append(n)
            elif token.isdigit():
                n = int(token)
                if n in recommended:
                    rec_apply.append(n)

        return {"recommended_to_apply": rec_apply, "skipped_to_apply": skip_apply, "skip_all": False}

    def test_all_applies_only_recommended(self):
        result = self.resolve_selection("all", recommended=[1, 2], skipped_keys=[1])
        assert result["recommended_to_apply"] == [1, 2]
        assert result["skipped_to_apply"] == []
        assert result["skip_all"] is False

    def test_s_prefix_applies_skipped(self):
        result = self.resolve_selection("S1", recommended=[1], skipped_keys=[1])
        assert result["skipped_to_apply"] == [1]
        assert result["recommended_to_apply"] == []

    def test_mixed_recommended_and_skipped(self):
        result = self.resolve_selection("1,S1", recommended=[1, 2], skipped_keys=[1])
        assert 1 in result["recommended_to_apply"]
        assert 1 in result["skipped_to_apply"]

    def test_skip_applies_nothing(self):
        result = self.resolve_selection("skip", recommended=[1, 2], skipped_keys=[1])
        assert result["skip_all"] is True
        assert result["recommended_to_apply"] == []
        assert result["skipped_to_apply"] == []
