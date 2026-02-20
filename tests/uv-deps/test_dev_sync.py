"""Tests for uv sync flag detection in uv-deps skill."""

import pytest

from conftest import detect_sync_flag, generate_pyproject_toml


class TestBareSync:
    """Test projects with no dev dependency group → bare uv sync."""

    def test_only_main_deps_returns_bare(self):
        content = generate_pyproject_toml("test", deps=["fastapi", "pydantic"])
        assert detect_sync_flag(content) == ""

    def test_no_sections_returns_bare(self):
        content = '[project]\nname = "test"\nversion = "0.1.0"\n'
        assert detect_sync_flag(content) == ""


class TestOptionalDependencies:
    """Test [project.optional-dependencies] dev → uv sync --extra dev."""

    def test_optional_dev_returns_extra_flag(self):
        content = generate_pyproject_toml("test", deps=["fastapi"], optional_dev=["pytest"])
        assert detect_sync_flag(content) == "--extra dev"

    def test_optional_dev_only_no_main_deps(self):
        """Should detect dev extras even when there are no main deps."""
        content = generate_pyproject_toml("test", optional_dev=["pytest", "ruff"])
        assert detect_sync_flag(content) == "--extra dev"

    def test_optional_dev_with_multiple_dev_packages(self):
        content = generate_pyproject_toml("test", deps=["fastapi"], optional_dev=["pytest", "ruff", "mypy"])
        assert detect_sync_flag(content) == "--extra dev"


class TestDependencyGroups:
    """Test [dependency-groups] dev → uv sync --group dev (PEP 735)."""

    def test_group_dev_returns_group_flag(self):
        content = generate_pyproject_toml("test", deps=["fastapi"], group_dev=["pytest"])
        assert detect_sync_flag(content) == "--group dev"

    def test_group_dev_only_no_main_deps(self):
        """Should detect group dev even when there are no main deps."""
        content = generate_pyproject_toml("test", group_dev=["pytest", "ruff"])
        assert detect_sync_flag(content) == "--group dev"


class TestFromFixture:
    """Test sync flag detection against fixture pyproject.toml files."""

    def test_bare_sync_fixture(self, use_fixture):
        project = use_fixture("sync-flags/bare")
        content = (project / "pyproject.toml").read_text()
        assert detect_sync_flag(content) == ""

    def test_optional_dev_fixture(self, use_fixture):
        project = use_fixture("sync-flags/optional-dev")
        content = (project / "pyproject.toml").read_text()
        assert detect_sync_flag(content) == "--extra dev"

    def test_group_dev_fixture(self, use_fixture):
        project = use_fixture("sync-flags/group-dev")
        content = (project / "pyproject.toml").read_text()
        assert detect_sync_flag(content) == "--group dev"
