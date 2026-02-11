"""Tests for edge cases in js-deps skill."""

import json
import os
import subprocess
import sys

import pytest

from conftest import (
    detect_package_manager,
    detect_package_manager_field,
    detect_validation_scripts,
    generate_package_json,
    run_package_discovery_script,
    run_pm_detection_script,
)


class TestNoPackageJson:
    """Test behavior when no package.json exists."""

    def test_discovery_returns_empty(self, use_fixture):
        """Package discovery should return empty for project without package.json."""
        project = use_fixture("package-discovery/empty")
        found = run_package_discovery_script(project)
        assert found == []

    def test_pm_defaults_to_npm(self, use_fixture):
        """PM detection should still default to npm without package.json."""
        project = use_fixture("package-discovery/empty")
        assert run_pm_detection_script(project) == "npm"

    def test_pm_field_returns_none(self, use_fixture):
        """packageManager field detection should return None without package.json."""
        project = use_fixture("package-discovery/empty")
        assert detect_package_manager_field(project) is None


class TestMalformedPackageJson:
    """Test handling of malformed package.json files."""

    def test_malformed_json_detected_by_discovery(self, use_fixture):
        """Malformed package.json should still be found by discovery."""
        project = use_fixture("edge-cases/malformed-json")
        found = run_package_discovery_script(project)
        assert "./package.json" in found

    def test_malformed_json_pm_field_returns_none(self, use_fixture):
        """packageManager field detection should handle malformed JSON."""
        project = use_fixture("edge-cases/malformed-json")
        assert detect_package_manager_field(project) is None

    def test_empty_package_json_detected(self, use_fixture):
        """Empty {} package.json should be found by discovery."""
        project = use_fixture("edge-cases/empty-package-json")
        found = run_package_discovery_script(project)
        assert "./package.json" in found


class TestValidationScripts:
    """Test detection of validation scripts from package.json (SKILL.md step 7)."""

    def test_detects_all_scripts(self, use_fixture):
        """Should detect build, lint, and test scripts."""
        project = use_fixture("validation/all-scripts")
        scripts = detect_validation_scripts(project / "package.json")
        assert scripts["build"] == "build"
        assert scripts["lint"] == "lint"
        assert scripts["test"] == "test"

    def test_detects_partial_scripts(self, use_fixture):
        """Should detect available scripts, None for missing."""
        project = use_fixture("validation/partial-scripts")
        scripts = detect_validation_scripts(project / "package.json")
        assert scripts["build"] == "build"
        assert scripts["lint"] is None
        assert scripts["test"] == "test"

    def test_no_scripts(self, use_fixture):
        """Should return all None when no scripts exist."""
        project = use_fixture("validation/no-scripts")
        scripts = detect_validation_scripts(project / "package.json")
        assert scripts["build"] is None
        assert scripts["lint"] is None
        assert scripts["test"] is None

    def test_detects_alternative_names(self, use_fixture):
        """Should detect alternative script names (compile, check, vitest)."""
        project = use_fixture("validation/alt-names")
        scripts = detect_validation_scripts(project / "package.json")
        assert scripts["build"] == "compile"
        assert scripts["lint"] == "check"
        assert scripts["test"] == "vitest"

    def test_ignores_non_validation_scripts(self, use_fixture):
        """Should not match dev/start scripts as validation."""
        project = use_fixture("validation/dev-only")
        scripts = detect_validation_scripts(project / "package.json")
        assert scripts["build"] is None
        assert scripts["lint"] is None
        assert scripts["test"] is None

    def test_missing_file_returns_none(self, temp_dir):
        """Should handle missing package.json gracefully."""
        scripts = detect_validation_scripts(temp_dir / "package.json")
        assert scripts == {"build": None, "lint": None, "test": None}


class TestNoDependencies:
    """Test package.json with no dependencies."""

    def test_empty_deps_discovered(self, use_fixture):
        """Package.json with no deps should still be discovered."""
        project = use_fixture("edge-cases/no-deps")
        found = run_package_discovery_script(project)
        assert "./package.json" in found

    def test_validation_still_works(self, use_fixture):
        """Validation scripts should work even without dependencies."""
        project = use_fixture("edge-cases/no-deps")
        scripts = detect_validation_scripts(project / "package.json")
        assert scripts["build"] == "build"


class TestPackageManagerFieldEdgeCases:
    """Test edge cases in packageManager field parsing."""

    def test_field_without_version(self, use_fixture):
        """packageManager: 'yarn' (no @version) should still parse."""
        project = use_fixture("edge-cases/pm-no-version")
        assert detect_package_manager_field(project) == "yarn"

    def test_empty_package_json_object(self, use_fixture):
        """Empty {} package.json should return None for PM field."""
        project = use_fixture("edge-cases/empty-package-json")
        assert detect_package_manager_field(project) is None


class TestNotGitRepo:
    """Test behavior outside a git repo."""

    def test_worktree_fails_outside_git(self, temp_dir):
        """git worktree should fail when not in a git repo."""
        (temp_dir / "package.json").write_text(generate_package_json("test"))
        result = subprocess.run(
            ["git", "worktree", "list"],
            cwd=temp_dir,
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0


class TestSymlinks:
    """Test handling of symlinked package.json files."""

    def test_symlinked_package_json_not_found_by_type_f(self, temp_dir):
        """Symlinked package.json is not found by 'find -type f' (symlinks are type l)."""
        real_dir = temp_dir / "real"
        real_dir.mkdir()
        (real_dir / "actual.json").write_text(generate_package_json("real"))
        (temp_dir / "package.json").symlink_to(real_dir / "actual.json")

        found = run_package_discovery_script(temp_dir)
        # find -type f doesn't follow symlinks; this documents the SKILL.md behavior
        assert found == []

    def test_real_package_json_alongside_symlink(self, temp_dir):
        """Real package.json should still be found when symlinks exist elsewhere."""
        (temp_dir / "package.json").write_text(generate_package_json("real"))
        sub = temp_dir / "linked"
        sub.mkdir()
        (sub / "package.json").symlink_to(temp_dir / "package.json")

        found = run_package_discovery_script(temp_dir)
        assert "./package.json" in found


class TestPermissions:
    """Test handling of permission issues."""

    @pytest.mark.skipif(
        sys.platform == "win32" or (hasattr(os, "geteuid") and os.geteuid() == 0),
        reason="Unix non-root only",
    )
    def test_unreadable_package_json(self, temp_dir):
        """Unreadable package.json should still be found by discovery."""
        pkg = temp_dir / "package.json"
        pkg.write_text(generate_package_json("test"))
        pkg.chmod(0o000)

        try:
            found = run_package_discovery_script(temp_dir)
            # find command finds files by name, doesn't need to read them
            assert "./package.json" in found
        finally:
            pkg.chmod(0o644)
