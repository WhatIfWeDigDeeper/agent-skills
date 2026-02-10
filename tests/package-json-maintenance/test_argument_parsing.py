"""Tests for argument parsing in package-json-maintenance skill."""

import json

import pytest

from conftest import parse_arguments


SAMPLE_DEPS = {
    "react": "^18.2.0",
    "express": "^4.18.2",
    "@testing-library/react": "^14.0.0",
    "@testing-library/jest-dom": "^6.0.0",
    "jest": "^29.7.0",
    "jest-environment-jsdom": "^29.7.0",
    "lodash": "^4.17.21",
    "@types/jest": "^29.5.0",
    "@types/react": "^18.2.0",
    "typescript": "^5.3.0",
}


class TestSpecificPackages:
    """Test parsing of specific package names."""

    def test_single_package(self):
        """Single package name should return as-is."""
        result = parse_arguments("jest", SAMPLE_DEPS)
        assert result == ["jest"]

    def test_multiple_packages(self):
        """Multiple package names should all be returned."""
        result = parse_arguments("jest @types/jest", SAMPLE_DEPS)
        assert result == ["jest", "@types/jest"]

    def test_scoped_package(self):
        """Scoped package names should be handled correctly."""
        result = parse_arguments("@testing-library/react", SAMPLE_DEPS)
        assert result == ["@testing-library/react"]

    def test_package_not_in_deps(self):
        """Packages not in dependencies should still be returned (user intent)."""
        result = parse_arguments("unknown-pkg", SAMPLE_DEPS)
        assert result == ["unknown-pkg"]


class TestDotAll:
    """Test '.' argument for processing all packages."""

    def test_dot_returns_all_deps(self):
        """Dot argument should return all dependency names."""
        result = parse_arguments(".", SAMPLE_DEPS)
        assert len(result) == len(SAMPLE_DEPS)

    def test_dot_returns_sorted(self):
        """Dot argument should return sorted dependency names."""
        result = parse_arguments(".", SAMPLE_DEPS)
        assert result == sorted(SAMPLE_DEPS.keys())

    def test_dot_with_empty_deps(self):
        """Dot with no dependencies should return empty list."""
        result = parse_arguments(".", {})
        assert result == []


class TestGlobPatterns:
    """Test glob pattern expansion against dependencies."""

    def test_testing_library_glob(self):
        """@testing-library/* should match scoped packages."""
        result = parse_arguments("@testing-library/*", SAMPLE_DEPS)
        assert "@testing-library/react" in result
        assert "@testing-library/jest-dom" in result
        assert len(result) == 2

    def test_jest_star_glob(self):
        """jest* should match jest and jest-prefixed packages."""
        result = parse_arguments("jest*", SAMPLE_DEPS)
        assert "jest" in result
        assert "jest-environment-jsdom" in result
        assert len(result) == 2

    def test_types_glob(self):
        """@types/* should match all type packages."""
        result = parse_arguments("@types/*", SAMPLE_DEPS)
        assert "@types/jest" in result
        assert "@types/react" in result
        assert len(result) == 2

    def test_glob_no_matches(self):
        """Glob that matches nothing should return empty."""
        result = parse_arguments("@angular/*", SAMPLE_DEPS)
        assert result == []

    def test_mixed_glob_and_specific(self):
        """Mix of glob patterns and specific packages."""
        result = parse_arguments("@testing-library/* lodash", SAMPLE_DEPS)
        assert "@testing-library/react" in result
        assert "@testing-library/jest-dom" in result
        assert "lodash" in result
        assert len(result) == 3


class TestEmptyAndInvalid:
    """Test empty and edge case arguments."""

    def test_empty_string(self):
        """Empty string should return empty list."""
        result = parse_arguments("", SAMPLE_DEPS)
        assert result == []

    def test_whitespace_only(self):
        """Whitespace-only should return empty list."""
        result = parse_arguments("   ", SAMPLE_DEPS)
        assert result == []

    @pytest.mark.parametrize("args", [
        "react",
        "react express",
        ".",
        "@testing-library/*",
    ])
    def test_returns_list(self, args):
        """All argument forms should return a list."""
        result = parse_arguments(args, SAMPLE_DEPS)
        assert isinstance(result, list)


class TestFromFixture:
    """Test argument parsing using fixture data."""

    def test_parses_against_fixture_deps(self, use_fixture):
        """Should parse globs against actual fixture package.json dependencies."""
        project = use_fixture("arguments")
        pkg = json.loads((project / "package.json").read_text())
        all_deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}

        result = parse_arguments("@testing-library/*", all_deps)
        assert len(result) == 2
        assert all(dep.startswith("@testing-library/") for dep in result)
