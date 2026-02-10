"""Tests for package.json discovery in package-json-maintenance skill."""

from conftest import generate_package_json, run_package_discovery_script


class TestSinglePackage:
    """Test discovery of single package.json."""

    def test_finds_root_package_json(self, use_fixture):
        """Should find package.json at project root."""
        project = use_fixture("package-discovery/single")
        found = run_package_discovery_script(project)
        assert "./package.json" in found

    def test_returns_one_result(self, use_fixture):
        """Single project should return exactly one package.json."""
        project = use_fixture("package-discovery/single")
        found = run_package_discovery_script(project)
        assert len(found) == 1


class TestMonorepo:
    """Test discovery in monorepo layouts."""

    def test_finds_all_package_jsons(self, use_fixture):
        """Should find root + all workspace package.json files."""
        project = use_fixture("package-discovery/monorepo")
        found = run_package_discovery_script(project)
        assert len(found) == 3

    def test_finds_root(self, use_fixture):
        """Should include root package.json."""
        project = use_fixture("package-discovery/monorepo")
        found = run_package_discovery_script(project)
        assert "./package.json" in found

    def test_finds_workspace_packages(self, use_fixture):
        """Should find workspace package.json files."""
        project = use_fixture("package-discovery/monorepo")
        found = run_package_discovery_script(project)
        frontend = [f for f in found if "frontend" in f]
        backend = [f for f in found if "backend" in f]
        assert len(frontend) == 1
        assert len(backend) == 1


class TestNodeModulesExclusion:
    """Test that node_modules are properly excluded."""

    def test_excludes_node_modules(self, use_fixture):
        """Should not include package.json files from node_modules."""
        project = use_fixture("package-discovery/with-node-modules")
        found = run_package_discovery_script(project)
        node_module_files = [f for f in found if "node_modules" in f]
        assert node_module_files == []

    def test_still_finds_root(self, use_fixture):
        """Should still find root package.json when node_modules exist."""
        project = use_fixture("package-discovery/with-node-modules")
        found = run_package_discovery_script(project)
        assert "./package.json" in found
        assert len(found) == 1


class TestDeepNesting:
    """Test discovery with deeply nested packages."""

    def test_finds_all_nested(self, use_fixture):
        """Should find all package.json files regardless of depth."""
        project = use_fixture("package-discovery/deep-nesting")
        found = run_package_discovery_script(project)
        assert len(found) == 3

    def test_includes_deepest_package(self, use_fixture):
        """Should include the most deeply nested package.json."""
        project = use_fixture("package-discovery/deep-nesting")
        found = run_package_discovery_script(project)
        deep_files = [f for f in found if "sub" in f]
        assert len(deep_files) == 1


class TestEmptyProject:
    """Test discovery when no package.json exists."""

    def test_no_results_for_empty(self, use_fixture):
        """Should return empty list when no package.json exists."""
        project = use_fixture("package-discovery/empty")
        found = run_package_discovery_script(project)
        assert found == []


class TestDynamicLayouts:
    """Test discovery with dynamically created layouts."""

    def test_many_workspaces(self, temp_dir):
        """Should find package.json in many workspace directories."""
        (temp_dir / "package.json").write_text(generate_package_json("root"))
        for i in range(5):
            ws = temp_dir / "packages" / f"pkg-{i}"
            ws.mkdir(parents=True)
            (ws / "package.json").write_text(generate_package_json(f"pkg-{i}"))

        found = run_package_discovery_script(temp_dir)
        assert len(found) == 6  # root + 5 workspaces

    def test_mixed_node_modules_and_workspaces(self, temp_dir):
        """Should find workspaces but exclude nested node_modules."""
        (temp_dir / "package.json").write_text(generate_package_json("root"))
        ws = temp_dir / "packages" / "app"
        ws.mkdir(parents=True)
        (ws / "package.json").write_text(generate_package_json("app"))
        nm = ws / "node_modules" / "dep"
        nm.mkdir(parents=True)
        (nm / "package.json").write_text(generate_package_json("dep"))

        found = run_package_discovery_script(temp_dir)
        assert len(found) == 2  # root + app, not dep
        assert all("node_modules" not in f for f in found)
