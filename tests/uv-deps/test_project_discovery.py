"""Tests for pyproject.toml discovery in uv-deps skill."""

from pathlib import Path

from conftest import generate_pyproject_toml, has_dependency_section, run_project_discovery_script


class TestSingleProject:
    """Test discovery of a single pyproject.toml."""

    def test_finds_root_pyproject(self, use_fixture):
        """Should find pyproject.toml at project root."""
        project = use_fixture("project-discovery/single")
        found = run_project_discovery_script(project)
        assert "./pyproject.toml" in found

    def test_returns_one_result(self, use_fixture):
        """Single project should return exactly one pyproject.toml."""
        project = use_fixture("project-discovery/single")
        found = run_project_discovery_script(project)
        assert len(found) == 1


class TestMonorepo:
    """Test discovery in monorepo / multi-service layouts."""

    def test_finds_all_pyproject_tomls(self, use_fixture):
        """Should find root + all service pyproject.toml files."""
        project = use_fixture("project-discovery/monorepo")
        found = run_project_discovery_script(project)
        assert len(found) == 3

    def test_finds_root(self, use_fixture):
        """Should include root pyproject.toml."""
        project = use_fixture("project-discovery/monorepo")
        found = run_project_discovery_script(project)
        assert "./pyproject.toml" in found

    def test_finds_service_packages(self, use_fixture):
        """Should find nested service pyproject.toml files."""
        project = use_fixture("project-discovery/monorepo")
        found = run_project_discovery_script(project)
        api = [f for f in found if "api" in f]
        worker = [f for f in found if "worker" in f]
        assert len(api) == 1
        assert len(worker) == 1


class TestExcludedDirectories:
    """Test that SKILL.md step 3 exclusions work correctly."""

    def test_excludes_venv(self, use_fixture):
        project = use_fixture("project-discovery/excluded-dirs")
        found = run_project_discovery_script(project)
        assert not any(".venv" in f for f in found)

    def test_excludes_tox(self, use_fixture):
        project = use_fixture("project-discovery/excluded-dirs")
        found = run_project_discovery_script(project)
        assert not any(".tox" in f for f in found)

    def test_excludes_build(self, use_fixture):
        project = use_fixture("project-discovery/excluded-dirs")
        found = run_project_discovery_script(project)
        assert not any("/build/" in f for f in found)

    def test_excludes_dist(self, use_fixture):
        project = use_fixture("project-discovery/excluded-dirs")
        found = run_project_discovery_script(project)
        assert not any("/dist/" in f for f in found)

    def test_still_finds_root(self, use_fixture):
        """Exclusions should not prevent finding the project root."""
        project = use_fixture("project-discovery/excluded-dirs")
        found = run_project_discovery_script(project)
        assert "./pyproject.toml" in found
        assert len(found) == 1


class TestEmptyProject:
    """Test discovery when no pyproject.toml exists."""

    def test_no_results_for_empty(self, use_fixture):
        """Should return empty list when no pyproject.toml exists."""
        project = use_fixture("project-discovery/empty")
        found = run_project_discovery_script(project)
        assert found == []


class TestDependencySectionDetection:
    """Test has_dependency_section identifies valid uv-deps targets."""

    def test_project_deps_detected(self):
        content = generate_pyproject_toml("test", deps=["fastapi"])
        assert has_dependency_section(content) is True

    def test_optional_deps_detected(self):
        content = generate_pyproject_toml("test", optional_dev=["pytest"])
        assert has_dependency_section(content) is True

    def test_group_deps_detected(self):
        content = generate_pyproject_toml("test", group_dev=["pytest"])
        assert has_dependency_section(content) is True

    def test_tool_only_not_detected(self):
        """pyproject.toml with only tool config (no deps) is out of scope."""
        content = '[project]\nname = "tool-only"\nversion = "0.1.0"\n\n[tool.ruff]\nline-length = 88\n'
        assert has_dependency_section(content) is False

    def test_dynamic_layout(self, temp_dir):
        """Should find pyproject.toml in multiple nested directories."""
        (temp_dir / "pyproject.toml").write_text(generate_pyproject_toml("root", deps=["fastapi"]))
        for i in range(3):
            pkg = temp_dir / "packages" / f"svc-{i}"
            pkg.mkdir(parents=True)
            (pkg / "pyproject.toml").write_text(generate_pyproject_toml(f"svc-{i}", deps=["httpx"]))
        found = run_project_discovery_script(temp_dir)
        assert len(found) == 4  # root + 3 services
