"""Tests for workflow routing in js-deps skill."""

import pytest

from conftest import classify_workflow


class TestAuditRouting:
    """Test that security-related requests route to audit workflow."""

    @pytest.mark.parametrize("request_text", [
        "audit the dependencies",
        "run a security audit",
        "check for CVE issues",
        "fix vulnerabilities in our packages",
        "are there any vulnerability alerts",
        "fix security issues",
        "check for security problems",
    ])
    def test_audit_keywords(self, request_text):
        """Security-related keywords should route to audit workflow."""
        assert classify_workflow(request_text) == "audit"

    def test_audit_case_insensitive(self):
        """Keyword matching should be case-insensitive."""
        assert classify_workflow("Run AUDIT on packages") == "audit"
        assert classify_workflow("Check for CVE") == "audit"


class TestUpdateRouting:
    """Test that update-related requests route to update workflow."""

    @pytest.mark.parametrize("request_text", [
        "update all dependencies",
        "upgrade react to latest",
        "get latest versions",
        "modernize our dependencies",
    ])
    def test_update_keywords(self, request_text):
        """Update-related keywords should route to update workflow."""
        assert classify_workflow(request_text) == "update"

    def test_update_case_insensitive(self):
        """Keyword matching should be case-insensitive."""
        assert classify_workflow("UPDATE packages") == "update"
        assert classify_workflow("Get LATEST versions") == "update"


class TestAmbiguousRequests:
    """Test routing of ambiguous or mixed requests."""

    def test_audit_takes_precedence_when_mixed(self):
        """When both audit and update keywords present, audit wins (checked first)."""
        result = classify_workflow("audit and update dependencies")
        assert result == "audit"

    def test_unknown_without_keywords(self):
        """Requests without recognized keywords should return unknown."""
        result = classify_workflow("fix the build")
        assert result == "unknown"

    def test_empty_request(self):
        """Empty request should return unknown."""
        result = classify_workflow("")
        assert result == "unknown"

    @pytest.mark.parametrize("request_text", [
        "install new package",
        "add lodash to the project",
        "remove unused dependencies",
    ])
    def test_non_matching_requests(self, request_text):
        """Unrelated package requests should return unknown."""
        assert classify_workflow(request_text) == "unknown"
