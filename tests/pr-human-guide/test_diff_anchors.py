"""Tests for SHA-256 diff anchor generation in pr-human-guide skill."""

import pytest

from conftest import build_diff_link, compute_diff_anchor


class TestDiffAnchor:
    """Test SHA-256 anchor computation per SKILL.md Step 4."""

    def test_known_anchor_value(self):
        """Verify against the confirmed anchor from the security-changes eval run."""
        # Confirmed in benchmark.json eval 1 evidence:
        # SHA-256("src/auth/middleware.ts") == e67371ea...
        expected = "e67371ea94bae31fbe0781e9d8777c9b44a1471d7dbd27d444ecd73ac826eb82"
        assert compute_diff_anchor("src/auth/middleware.ts") == expected

    def test_different_paths_produce_different_anchors(self):
        a1 = compute_diff_anchor("src/auth/middleware.ts")
        a2 = compute_diff_anchor("src/components/UserCard.tsx")
        assert a1 != a2

    def test_anchor_is_64_hex_chars(self):
        """SHA-256 produces a 64-character lowercase hex string."""
        anchor = compute_diff_anchor("any/path/here.py")
        assert len(anchor) == 64
        assert all(c in "0123456789abcdef" for c in anchor)

    def test_no_trailing_newline_in_input(self):
        """printf '%s' does not append a newline — the hash must not include one."""
        without_newline = compute_diff_anchor("src/auth/middleware.ts")
        import hashlib
        with_newline = hashlib.sha256("src/auth/middleware.ts\n".encode()).hexdigest()
        assert without_newline != with_newline


class TestBuildDiffLink:
    """Test full GitHub diff link construction per SKILL.md Step 4."""

    def test_known_link_format(self):
        link = build_diff_link("owner", "repo", 42, "src/auth/middleware.ts")
        anchor = "e67371ea94bae31fbe0781e9d8777c9b44a1471d7dbd27d444ecd73ac826eb82"
        assert link == f"https://github.com/owner/repo/pull/42/files#diff-{anchor}"

    def test_link_contains_pr_number(self):
        link = build_diff_link("org", "project", 99, "path/to/file.ts")
        assert "/pull/99/" in link

    def test_link_contains_owner_and_repo(self):
        link = build_diff_link("myorg", "myrepo", 1, "file.ts")
        assert "github.com/myorg/myrepo" in link

    def test_link_contains_diff_prefix(self):
        link = build_diff_link("owner", "repo", 1, "file.ts")
        assert "#diff-" in link
