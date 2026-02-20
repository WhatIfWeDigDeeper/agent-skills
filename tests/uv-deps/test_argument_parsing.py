"""Tests for argument parsing in uv-deps skill."""

import pytest

from conftest import parse_arguments

SAMPLE_DEPS = {
    "fastapi": ">=0.100",
    "pydantic": ">=2.0",
    "sqlalchemy": ">=2.0",
    "django-rest-framework": ">=3.14",
    "django-filter": ">=23.0",
    "pytest": ">=7.0",
    "ruff": ">=0.1",
    "mypy": ">=1.0",
}


class TestSpecificPackages:
    """Test parsing of specific package names."""

    def test_single_package(self):
        """Single package name should return as-is."""
        result = parse_arguments("fastapi", SAMPLE_DEPS)
        assert result == ["fastapi"]

    def test_multiple_packages(self):
        """Multiple package names should all be returned."""
        result = parse_arguments("fastapi pydantic", SAMPLE_DEPS)
        assert result == ["fastapi", "pydantic"]

    def test_package_not_in_deps(self):
        """Packages not in dependencies should still be returned.

        The skill warns about unknown packages separately (step 5); the parser
        should not silently drop them.
        """
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

    def test_django_star_glob(self):
        """django-* should match all django-prefixed packages."""
        result = parse_arguments("django-*", SAMPLE_DEPS)
        assert "django-rest-framework" in result
        assert "django-filter" in result
        assert len(result) == 2

    def test_glob_no_matches(self):
        """Glob that matches nothing should return empty list."""
        result = parse_arguments("celery-*", SAMPLE_DEPS)
        assert result == []

    def test_mixed_glob_and_specific(self):
        """Mix of glob pattern and specific package name."""
        result = parse_arguments("django-* fastapi", SAMPLE_DEPS)
        assert "django-rest-framework" in result
        assert "django-filter" in result
        assert "fastapi" in result
        assert len(result) == 3

    def test_glob_results_sorted(self):
        """Glob expansion results should be sorted."""
        result = parse_arguments("django-*", SAMPLE_DEPS)
        assert result == sorted(result)


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
        "fastapi",
        "fastapi pydantic",
        ".",
        "django-*",
    ])
    def test_always_returns_list(self, args):
        """All argument forms should return a list."""
        result = parse_arguments(args, SAMPLE_DEPS)
        assert isinstance(result, list)
